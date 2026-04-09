from sqlalchemy import (
    Column, String, Text, DateTime,
    Integer, ForeignKey, Enum as SAEnum
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class InteractionSeverity(str, enum.Enum):
    minor = "minor"
    moderate = "moderate"
    major = "major"

class Drug(Base):
    __tablename__ = "drugs"

    id = Column(String(10), primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    atc_code = Column(String(20), nullable=True, index=True) # mã ATC (Anatomical Therapeutic Chemical Classification System)
    description = Column(Text, nullable=True)
    dosage_form = Column(String(50), nullable=True) # viên nén, siro, tiêm, v.v.
    classification = Column(String(100), nullable=True) # thuốc kê đơn, không kê đơn, v.v.

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    products = relationship(
        "DrugProduct",
        back_populates="drug",
        cascade="all, delete-orphan"  # Xóa drug → tự xóa products
    )

    warnings = relationship(
        "DrugWarning",
        back_populates="drug",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Drug id={self.id} name={self.name}>"
    

# Thuốc cụ thương - sản phẩm thương mại
class DrugProduct(Base):
    __tablename__ = "drug_products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_id = Column(String(10), ForeignKey("drugs.id"), nullable=False, index=True)
    trade_name = Column(String(200), nullable=False)   # Tên thương mại
    route = Column(String(100), nullable=False)         # Đường dùng
    dosage = Column(String(100), nullable=False)        # Hàm lượng
    formulation = Column(String(100), nullable=False)   # Dạng bào chế
    origin = Column(String(100), nullable=False)        # Xuất xứ

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    drug = relationship("Drug", back_populates="products")


# Cảnh báo về thuốc
class DrugWarning(Base):
    __tablename__ = "drug_warnings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_id = Column(String(10), ForeignKey("drugs.id"), nullable=False, index=True)
    warning_text = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    drug = relationship("Drug", back_populates="warnings")


# Tương tác giữa 2 thuốc — sẽ dùng để kiểm tra khi người dùng nhập đơn thuốc
class DrugInteraction(Base):
    """Tương tác giữa 2 thuốc"""
    __tablename__ = "drug_interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # drug_id_1 luôn < drug_id_2 (lexicographic) để tránh duplicate
    # VD: (DB000001, DB000002) — không bao giờ có (DB000002, DB000001)
    drug_id_1 = Column(String(10), ForeignKey("drugs.id"), nullable=False)
    drug_id_2 = Column(String(10), ForeignKey("drugs.id"), nullable=False)
    interaction_type = Column(String(100), nullable=True)  # Loại tương tác
    severity = Column(
        SAEnum(InteractionSeverity),
        nullable=False,
        default=InteractionSeverity.moderate
    )
    description = Column(Text, nullable=True)     # Mô tả tương tác
    recommendation = Column(Text, nullable=True)   # Khuyến nghị

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )