# -*- coding: utf-8 -*-
"""
inference.py — DDI Prediction Engine
======================================
DDIPredictor: load artifacts từ train.py và dự đoán tương tác thuốc.

Cách dùng:
    predictor = DDIPredictor("models/")
    result = predictor.predict_prescription(["Aspirin", "Warfarin", "Ibuprofen"])
    print(result)
"""

import json
import pickle
import itertools
import numpy as np

from pathlib import Path
from typing import List, Dict, Any


# ─────────────────────────────────────────────────────────────────────────────
# PREDICTOR
# ─────────────────────────────────────────────────────────────────────────────

class DDIPredictor:
    """
    Drug-Drug Interaction Predictor.

    Loads model artifacts và cung cấp API dự đoán cho một đơn thuốc.
    """

    # Confidence threshold: cặp thuốc có max softmax >= threshold
    # được coi là "có tương tác đáng chú ý"
    DEFAULT_THRESHOLD = 0.40

    def __init__(self, model_dir: str = "models/", threshold: float = None):
        """
        Parameters
        ----------
        model_dir   : thư mục chứa artifacts từ train.py
        threshold   : ngưỡng confidence (0-1), mặc định 0.40
        """
        self.model_dir  = Path(model_dir)
        self.threshold  = threshold if threshold is not None else self.DEFAULT_THRESHOLD

        self._model     = None
        self._drug2vec  = None
        self._id2label  = None
        self._label_map = None
        self._num_classes = None

        self._load_artifacts()

    # ── Private: load ────────────────────────────────────────────────────────

    def _load_artifacts(self):
        """Load model, drug2vec và label_map từ model_dir."""
        import tensorflow as tf  # lazy import

        model_path    = self.model_dir / "ModernDDIMDL.keras"
        drug2vec_path = self.model_dir / "drug2vec.pkl"
        label_path    = self.model_dir / "label_map.json"

        for p in [model_path, drug2vec_path, label_path]:
            if not p.exists():
                raise FileNotFoundError(
                    f"Artifact không tìm thấy: {p}\n"
                    "Hãy chạy train.py trước."
                )

        print(f"[DDIPredictor] Loading model from {model_path}...")
        self._model = tf.keras.models.load_model(str(model_path))

        print(f"[DDIPredictor] Loading drug2vec from {drug2vec_path}...")
        with open(drug2vec_path, "rb") as f:
            self._drug2vec = pickle.load(f)

        print(f"[DDIPredictor] Loading label map from {label_path}...")
        with open(label_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        self._label_map   = meta["label_map"]          # label_string → int
        self._id2label    = {
            int(k): v for k, v in meta["id2label"].items()
        }                                               # int → label_string
        self._num_classes = meta["num_classes"]

        print(
            f"[DDIPredictor] Ready — "
            f"{len(self._drug2vec)} drugs | "
            f"{self._num_classes} interaction classes"
        )

    # ── Private: pair embedding ──────────────────────────────────────────────

    @staticmethod
    def _build_pair_embedding(v1: np.ndarray, v2: np.ndarray) -> np.ndarray:
        """4-way pair: [v1 || v2 || |v1-v2| || v1*v2]"""
        return np.concatenate([v1, v2, np.abs(v1 - v2), v1 * v2])

    # ── Public API ───────────────────────────────────────────────────────────

    def list_known_drugs(self) -> List[str]:
        """Trả về danh sách tên thuốc trong training database."""
        return sorted(self._drug2vec.keys())

    def predict_prescription(
        self,
        drug_list: List[str],
        threshold: float = None,
    ) -> Dict[str, Any]:
        """
        Dự đoán tương tác thuốc cho một đơn thuốc.

        Parameters
        ----------
        drug_list : danh sách tên thuốc (case-sensitive, khớp với training data)
        threshold : override ngưỡng confidence mặc định

        Returns
        -------
        {
          "has_interaction": bool,
          "total_pairs_checked": int,
          "unknown_drugs": [...],
          "interactions": [
            {
              "drug_a": str,
              "drug_b": str,
              "label": str,           # mô tả loại tương tác
              "confidence": float,    # [0,1] max softmax probability
              "top3_predictions": [   # top-3 dự đoán (label, confidence)
                {"label": str, "confidence": float},
                ...
              ]
            }
          ]
        }
        """
        thresh = threshold if threshold is not None else self.threshold

        # Kiểm tra thuốc không có trong database
        unknown = [d for d in drug_list if d not in self._drug2vec]
        known   = [d for d in drug_list if d in self._drug2vec]

        # Tạo tất cả cặp từ danh sách thuốc đã biết
        pairs = list(itertools.combinations(known, 2))

        if not pairs:
            return {
                "has_interaction": False,
                "total_pairs_checked": 0,
                "unknown_drugs": unknown,
                "interactions": [],
                "message": (
                    "Không đủ thuốc đã biết để kiểm tra."
                    if len(known) < 2
                    else "Không có cặp nào để kiểm tra."
                ),
            }

        # Build pair embeddings
        pair_embeddings = np.array([
            self._build_pair_embedding(
                self._drug2vec[a],
                self._drug2vec[b],
            )
            for a, b in pairs
        ])

        # Predict
        pred_probs = self._model.predict(pair_embeddings, verbose=0)  # (n_pairs, 65)

        # Parse results
        interactions = []
        for (drug_a, drug_b), probs in zip(pairs, pred_probs):
            top_idx = int(np.argmax(probs))
            confidence = float(probs[top_idx])

            # Top-3 predictions
            top3_idx = np.argsort(probs)[::-1][:3]
            top3 = [
                {
                    "label": self._id2label[int(i)],
                    "confidence": round(float(probs[i]), 4),
                }
                for i in top3_idx
            ]

            if confidence >= thresh:
                interactions.append({
                    "drug_a": drug_a,
                    "drug_b": drug_b,
                    "label": self._id2label[top_idx],
                    "confidence": round(confidence, 4),
                    "top3_predictions": top3,
                })

        # Sort by confidence descending
        interactions.sort(key=lambda x: x["confidence"], reverse=True)

        return {
            "has_interaction": len(interactions) > 0,
            "total_pairs_checked": len(pairs),
            "unknown_drugs": unknown,
            "interactions": interactions,
        }

    def predict_pair(
        self,
        drug_a: str,
        drug_b: str,
    ) -> Dict[str, Any]:
        """
        Dự đoán tương tác cho một cặp thuốc cụ thể.
        Trả về toàn bộ 65 predictions (sorted by confidence).
        """
        missing = [d for d in [drug_a, drug_b] if d not in self._drug2vec]
        if missing:
            return {
                "error": f"Thuốc không có trong database: {missing}",
                "unknown_drugs": missing,
            }

        pair_emb = self._build_pair_embedding(
            self._drug2vec[drug_a],
            self._drug2vec[drug_b],
        ).reshape(1, -1)

        probs = self._model.predict(pair_emb, verbose=0)[0]

        predictions = [
            {
                "rank": i + 1,
                "label": self._id2label[int(idx)],
                "confidence": round(float(probs[idx]), 4),
            }
            for i, idx in enumerate(np.argsort(probs)[::-1])
        ]

        top = predictions[0]

        return {
            "drug_a": drug_a,
            "drug_b": drug_b,
            "predicted_label": top["label"],
            "confidence": top["confidence"],
            "has_significant_interaction": top["confidence"] >= self.threshold,
            "all_predictions": predictions,
        }
