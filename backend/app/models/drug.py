import enum

from sqlalchemy import (
    Column, String, Text, DateTime,
    Integer, ForeignKey, UniqueConstraint, PrimaryKeyConstraint,
    Float, Enum as SAEnum,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class InteractionSource(str, enum.Enum):
    database = "database"
    model_predicted = "model_predicted"


class Drug(Base):
    __tablename__ = "drugs"

    id = Column(String(50), primary_key=True, index=True)
    generic_name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    chemical_formula = Column(String(255), nullable=True)
    molecular_formula = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    warnings = relationship(
        "DrugWarning",
        back_populates="drug",
        cascade="all, delete-orphan"
    )
    dosage_forms = relationship(
        "DrugDosageForm",
        back_populates="drug",
        cascade="all, delete-orphan"
    )
    categories = relationship(
        "DrugCategory",
        back_populates="drug",
        cascade="all, delete-orphan"
    )
    atc_codes = relationship(
        "DrugAtcCode",
        back_populates="drug",
        cascade="all, delete-orphan"
    )
    interactions = relationship(
        "DrugInteraction",
        back_populates="drug",
        cascade="all, delete-orphan"
    )
    features = relationship(
        "DrugFeature",
        back_populates="drug",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Drug id={self.id} generic_name={self.generic_name}>"


# Cảnh báo về thuốc
class DrugWarning(Base):
    __tablename__ = "drug_warnings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_id = Column(String(50), ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    warning_text = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    drug = relationship("Drug", back_populates="warnings")


# Dạng bào chế (1 thuốc - nhiều dạng)
class DrugDosageForm(Base):
    __tablename__ = "drug_dosage_forms"

    drug_id = Column(String(50), ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    dosage_form = Column(String(255), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("drug_id", "dosage_form"),
    )

    drug = relationship("Drug", back_populates="dosage_forms")


# Nhóm dược lý / phân loại (1 thuốc - nhiều nhóm)
class DrugCategory(Base):
    __tablename__ = "drug_categories"

    drug_id = Column(String(50), ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    category_name = Column(String(255), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("drug_id", "category_name"),
    )

    drug = relationship("Drug", back_populates="categories")


# Mã ATC (1 thuốc - nhiều mã ATC)
class DrugAtcCode(Base):
    __tablename__ = "drug_atc_codes"

    drug_id = Column(String(50), ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    atc_code = Column(String(50), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("drug_id", "atc_code"),
    )

    drug = relationship("Drug", back_populates="atc_codes")


# Tương tác giữa 2 thuốc
# interacts_with_id KHÔNG có FK vì data nguồn có thể chứa ID chưa có trong DB
class DrugInteraction(Base):
    __tablename__ = "drug_interactions"

    drug_id = Column(String(50), ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    interacts_with_id = Column(String(50), nullable=False, index=True)
    interacts_with_name = Column(String(255), nullable=True)
    event_type_id = Column(
        Integer,
        ForeignKey("drug_event_types.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    interaction_label = Column(String(255), nullable=True, index=True)
    source = Column(
        SAEnum(InteractionSource, name="interactionsource"),
        nullable=True,
        index=True,
    )
    confidence_score = Column(Float, nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint("drug_id", "interacts_with_id"),
    )

    drug = relationship("Drug", back_populates="interactions")
    event_type = relationship("DrugEventType", back_populates="interactions")

    def __repr__(self):
        return f"<DrugInteraction {self.drug_id} ↔ {self.interacts_with_id}>"
