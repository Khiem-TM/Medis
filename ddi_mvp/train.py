# -*- coding: utf-8 -*-
"""
train.py — DDI-MVP Training Pipeline
=====================================
Kết hợp feature pipeline từ feature_processing.py
với kiến trúc ModernDDIMDL từ DDIMLD_v2.ipynb

Artifacts đầu ra (lưu vào thư mục models/):
  - drug2vec.pkl      : dict {drug_name: np.array(1024,)}
  - label_map.json    : {encoded_label: "label_string", ...}
  - feature_config.json : PCA params metadata
  - ModernDDIMDL.keras : trained model weights

Cách dùng:
  python train.py --db path/to/event.db --output models/
  python train.py --db event.db --epochs 50 --batch_size 128
"""

import os
import json
import pickle
import sqlite3
import argparse
import numpy as np
import pandas as pd
import torch

from pathlib import Path
from pandas import DataFrame
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report, accuracy_score
from transformers import AutoTokenizer, AutoModel

import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Input, Dense, Dropout, BatchNormalization, Activation,
    Add, MultiHeadAttention, GlobalAveragePooling1D, Reshape,
)
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

SEED        = 42
EVENT_NUM   = 65

# Kích thước PCA cho từng loại feature (giống feature_processing.py)
TARGET_DIM  = 128
ENZYME_DIM  = 64
PATHWAY_DIM = 64
SMILES_DIM  = 768   # ChemBERTa CLS-pooled output

# Tổng chiều mỗi drug: 768 + 128 + 64 + 64 = 1024
DRUG_VEC_DIM = SMILES_DIM + TARGET_DIM + ENZYME_DIM + PATHWAY_DIM

# Pair embedding = [v1 || v2 || |v1-v2| || v1*v2] = 4 * 1024 = 4096
PAIR_VEC_DIM = DRUG_VEC_DIM * 4

CHEMBERTA_MODEL = "seyonec/ChemBERTa-zinc-base-v1"


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────────────────────

def jaccard_similarity(matrix: np.ndarray) -> np.ndarray:
    """Tính Jaccard similarity matrix từ binary feature matrix."""
    matrix = np.asarray(matrix, dtype=float)
    numerator = np.dot(matrix, matrix.T)
    denominator = (
        np.ones(matrix.shape) @ matrix.T
        + matrix @ np.ones(matrix.T.shape)
        - numerator
    )
    denominator[denominator == 0] = 1e-10
    return numerator / denominator


def build_jaccard_pca_vector(
    feature_name: str,
    df: pd.DataFrame,
    vector_size: int,
    seed: int = SEED,
) -> np.ndarray:
    """
    Xây dựng feature embedding bằng Jaccard Similarity + PCA.
    Dùng cho: target, enzyme, pathway.
    """
    all_features = []
    drug_feature_list = df[feature_name].tolist()

    for item in drug_feature_list:
        if pd.isna(item):
            continue
        for feat in str(item).split("|"):
            if feat not in all_features:
                all_features.append(feat)

    feature_matrix = np.zeros((len(drug_feature_list), len(all_features)), dtype=float)
    df_feat = DataFrame(feature_matrix, columns=all_features)

    for i, item in enumerate(drug_feature_list):
        if pd.isna(item):
            continue
        for feat in str(item).split("|"):
            df_feat.loc[i, feat] = 1.0

    sim_matrix = jaccard_similarity(np.array(df_feat))

    pca = PCA(n_components=min(vector_size, sim_matrix.shape[1]), random_state=seed)
    result = pca.fit_transform(sim_matrix)

    # Pad nếu PCA ra ít thành phần hơn vector_size
    if result.shape[1] < vector_size:
        pad = np.zeros((result.shape[0], vector_size - result.shape[1]))
        result = np.hstack([result, pad])

    return result, pca


def build_chemberta_embeddings(
    df_drug: pd.DataFrame,
    model_name: str = CHEMBERTA_MODEL,
) -> np.ndarray:
    """
    Sinh SMILES embedding cho từng drug bằng ChemBERTa (mean pooling).
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  [ChemBERTa] Loading model on {device}...")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    bert_model = AutoModel.from_pretrained(model_name).to(device)
    bert_model.eval()

    embeddings = []

    with torch.no_grad():
        for idx, row in df_drug.iterrows():
            smiles = row.get("smile", None)

            if pd.isna(smiles) or not smiles:
                embeddings.append(np.zeros(SMILES_DIM))
                continue

            try:
                inputs = tokenizer(
                    str(smiles),
                    return_tensors="pt",
                    truncation=True,
                    padding=True,
                    max_length=128,
                )
                inputs = {k: v.to(device) for k, v in inputs.items()}
                out = bert_model(**inputs)
                emb = out.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
                embeddings.append(emb)
            except Exception as e:
                print(f"  [WARN] SMILES error at idx={idx}: {e}")
                embeddings.append(np.zeros(SMILES_DIM))

            if idx % 100 == 0:
                print(f"  [ChemBERTa] {idx}/{len(df_drug)} drugs processed")

    del bert_model
    torch.cuda.empty_cache()

    return np.array(embeddings)


def build_drug2vec(df_drug: pd.DataFrame) -> tuple[dict, dict]:
    """
    Xây dựng drug2vec: {drug_name → np.array(1024,)}.
    Trả về (drug2vec, pca_objects) để dùng cho inference sau này.
    """
    print("\n[1/4] Building ChemBERTa SMILES embeddings (768d)...")
    smiles_emb = build_chemberta_embeddings(df_drug)
    print(f"  smiles_emb shape: {smiles_emb.shape}")

    print("\n[2/4] Building Target embeddings (Jaccard+PCA 128d)...")
    target_emb, pca_target = build_jaccard_pca_vector("target", df_drug, TARGET_DIM)
    print(f"  target_emb shape: {target_emb.shape}")

    print("\n[3/4] Building Enzyme embeddings (Jaccard+PCA 64d)...")
    enzyme_emb, pca_enzyme = build_jaccard_pca_vector("enzyme", df_drug, ENZYME_DIM)
    print(f"  enzyme_emb shape: {enzyme_emb.shape}")

    print("\n[4/4] Building Pathway embeddings (Jaccard+PCA 64d)...")
    pathway_emb, pca_pathway = build_jaccard_pca_vector("pathway", df_drug, PATHWAY_DIM)
    print(f"  pathway_emb shape: {pathway_emb.shape}")

    # Concatenate: [SMILES || Target || Enzyme || Pathway] = 1024d
    drug_vectors = np.concatenate([smiles_emb, target_emb, enzyme_emb, pathway_emb], axis=1)
    print(f"\n  Final drug vector shape: {drug_vectors.shape}")

    drug2vec = {}
    for i, row in df_drug.iterrows():
        drug2vec[row["name"]] = drug_vectors[i]

    pca_objects = {
        "target": pca_target,
        "enzyme": pca_enzyme,
        "pathway": pca_pathway,
    }

    return drug2vec, pca_objects


def build_pair_embedding(v1: np.ndarray, v2: np.ndarray) -> np.ndarray:
    """
    4-way pair embedding: [v1 || v2 || |v1-v2| || v1*v2]
    """
    return np.concatenate([v1, v2, np.abs(v1 - v2), v1 * v2])


def build_dataset(
    df_extraction: pd.DataFrame,
    drug2vec: dict,
) -> tuple[np.ndarray, np.ndarray, dict, dict]:
    """
    Xây dựng (X, y) từ extraction table.
    Trả về X, y, label_map (label_string → int), id2label (int → label_string).
    """
    # Tạo label từ mechanism + action
    df_extraction = df_extraction.copy()
    df_extraction["label"] = (
        df_extraction["mechanism"].str.strip()
        + " "
        + df_extraction["action"].str.strip()
    )

    # Encode label theo tần suất (giống feature_processing.py)
    label_counts = (
        df_extraction.groupby("label")
        .size()
        .reset_index(name="freq")
        .sort_values("freq", ascending=False)
        .reset_index(drop=True)
    )
    label_map  = {row["label"]: idx for idx, row in label_counts.iterrows()}
    id2label   = {idx: row["label"] for idx, row in label_counts.iterrows()}

    X, y = [], []
    skipped = 0

    for _, row in df_extraction.iterrows():
        drug_a = row["drugA"]
        drug_b = row["drugB"]

        if drug_a not in drug2vec or drug_b not in drug2vec:
            skipped += 1
            continue

        pair_emb = build_pair_embedding(drug2vec[drug_a], drug2vec[drug_b])
        X.append(pair_emb)
        y.append(label_map[row["label"]])

    print(f"\n  Dataset built: {len(X)} pairs | Skipped (unknown drug): {skipped}")
    print(f"  Number of classes: {len(label_map)}")

    return np.array(X), np.array(y), label_map, id2label


# ─────────────────────────────────────────────────────────────────────────────
# MODEL ARCHITECTURE  (ModernDDIMDL từ DDIMLD_v2.ipynb)
# ─────────────────────────────────────────────────────────────────────────────

def residual_block(x, units: int, dropout: float = 0.3):
    """Residual block: Dense → BN → Dropout → Dense → BN → Add → ReLU"""
    shortcut = x
    x = Dense(units, activation="relu")(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout)(x)
    x = Dense(units)(x)
    x = BatchNormalization()(x)
    x = Add()([shortcut, x])
    x = Activation("relu")(x)
    return x


def attention_block(x):
    """Multi-Head Self-Attention block."""
    x_reshape = Reshape((1, int(x.shape[-1])))(x)
    attention = MultiHeadAttention(num_heads=4, key_dim=32)(x_reshape, x_reshape)
    attention = GlobalAveragePooling1D()(attention)
    return attention


def build_modern_ddimdl(input_dim: int, num_classes: int) -> Model:
    """
    ModernDDIMDL:
      Input(4096)
        → Dense(1024) → BN → Dropout(0.4)
        → Dense(512) → BN
        → ResidualBlock(512) × 2
        → MultiHeadAttention
        → Dense(256) → BN → Dropout(0.3)
        → Dense(num_classes, softmax)
    """
    inputs = Input(shape=(input_dim,), name="pair_embedding")

    # Feature Projection
    x = Dense(1024, activation="relu", name="proj_1")(inputs)
    x = BatchNormalization(name="bn_1")(x)
    x = Dropout(0.4, name="drop_1")(x)

    x = Dense(512, activation="relu", name="proj_2")(x)
    x = BatchNormalization(name="bn_2")(x)

    # Residual Learning
    x = residual_block(x, 512)
    x = residual_block(x, 512)

    # Attention
    x = attention_block(x)

    # Classifier Head
    x = Dense(256, activation="relu", name="head_dense")(x)
    x = BatchNormalization(name="head_bn")(x)
    x = Dropout(0.3, name="head_drop")(x)

    outputs = Dense(num_classes, activation="softmax", name="output")(x)

    model = Model(inputs=inputs, outputs=outputs, name="ModernDDIMDL")

    model.compile(
        optimizer=Adam(learning_rate=1e-3),
        loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
        metrics=["accuracy"],
    )

    return model


# ─────────────────────────────────────────────────────────────────────────────
# TRAINING
# ─────────────────────────────────────────────────────────────────────────────

def train(args):
    np.random.seed(SEED)
    tf.random.set_seed(SEED)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Load data ──────────────────────────────────────────────────────────
    print("=" * 60)
    print("Loading data from:", args.db)
    conn = sqlite3.connect(args.db)

    df_drug       = pd.read_sql("SELECT * FROM drug;", conn)
    df_extraction = pd.read_sql("SELECT * FROM extraction;", conn)
    conn.close()

    print(f"  Drugs: {len(df_drug)}")
    print(f"  Interaction pairs: {len(df_extraction)}")

    # ── Build drug2vec ──────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("Building drug feature vectors...")
    drug2vec, pca_objects = build_drug2vec(df_drug)

    # Save drug2vec
    drug2vec_path = output_dir / "drug2vec.pkl"
    with open(drug2vec_path, "wb") as f:
        pickle.dump(drug2vec, f)
    print(f"\n  Saved drug2vec → {drug2vec_path}")

    # Save PCA objects (for inference on new drugs)
    pca_path = output_dir / "pca_objects.pkl"
    with open(pca_path, "wb") as f:
        pickle.dump(pca_objects, f)

    # ── Build dataset ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("Building pair embeddings and labels...")
    X, y, label_map, id2label = build_dataset(df_extraction, drug2vec)

    # Save label map
    label_map_path = output_dir / "label_map.json"
    with open(label_map_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "label_map": label_map,        # {label_string: int}
                "id2label": {str(k): v for k, v in id2label.items()},  # {int: label_string}
                "num_classes": len(label_map),
                "drug_vec_dim": DRUG_VEC_DIM,
                "pair_vec_dim": PAIR_VEC_DIM,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"  Saved label_map → {label_map_path}")

    # ── Train/test split ────────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED
    )
    print(f"\n  Train: {X_train.shape} | Test: {X_test.shape}")

    num_classes = len(id2label)
    y_train_oh  = tf.keras.utils.to_categorical(y_train, num_classes)
    y_test_oh   = tf.keras.utils.to_categorical(y_test, num_classes)

    # Class weights (xử lý long-tail)
    class_weights = compute_class_weight(
        class_weight="balanced",
        classes=np.unique(y_train),
        y=y_train,
    )
    class_weight_dict = dict(enumerate(class_weights))

    # ── Build & train model ─────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("Building ModernDDIMDL...")
    model = build_modern_ddimdl(input_dim=PAIR_VEC_DIM, num_classes=num_classes)
    model.summary()

    callbacks = [
        EarlyStopping(
            monitor="val_loss",
            patience=8,
            restore_best_weights=True,
            verbose=1,
        ),
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            verbose=1,
        ),
    ]

    print("\nTraining...")
    history = model.fit(
        X_train,
        y_train_oh,
        validation_split=0.1,
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=callbacks,
        class_weight=class_weight_dict,
        verbose=1,
    )

    # ── Evaluate ────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    test_loss, test_acc = model.evaluate(X_test, y_test_oh, verbose=0)
    pred_probs   = model.predict(X_test, verbose=0)
    pred_classes = np.argmax(pred_probs, axis=1)

    print(f"\n  Test Accuracy : {test_acc:.4f}")
    print(f"  Test Loss     : {test_loss:.4f}")
    print("\nClassification Report (top classes):")
    print(
        classification_report(
            y_test,
            pred_classes,
            target_names=[id2label[i] for i in range(num_classes)],
            zero_division=0,
        )
    )

    # ── Save model ───────────────────────────────────────────────────────────
    model_path = output_dir / "ModernDDIMDL.keras"
    model.save(str(model_path))
    print(f"\n  Saved model → {model_path}")

    print("\n" + "=" * 60)
    print("Training complete. Artifacts saved to:", output_dir)
    print("  - drug2vec.pkl")
    print("  - pca_objects.pkl")
    print("  - label_map.json")
    print("  - ModernDDIMDL.keras")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train DDI-MVP model",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--db", type=str, default="event.db",
        help="Path to SQLite database (event.db)",
    )
    parser.add_argument(
        "--output", type=str, default="models/",
        help="Output directory for model artifacts",
    )
    parser.add_argument(
        "--epochs", type=int, default=100,
        help="Maximum training epochs (EarlyStopping applies)",
    )
    parser.add_argument(
        "--batch_size", type=int, default=128,
        help="Training batch size",
    )

    args = parser.parse_args()
    train(args)
