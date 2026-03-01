from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.sql import func
from app.models.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # policy, claim, payment
    entity_id = Column(Integer, nullable=False, index=True)
    document_type = Column(String(100), nullable=False)  # estimate, invoice, photo, medical_bill

    file_path = Column(String(1000), nullable=False)
    file_name = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)

    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
