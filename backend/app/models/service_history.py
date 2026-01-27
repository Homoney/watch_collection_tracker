import uuid
from sqlalchemy import Column, String, Text, Numeric, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class ServiceHistory(Base):
    __tablename__ = "service_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    watch_id = Column(UUID(as_uuid=True), ForeignKey("watches.id", ondelete="CASCADE"), nullable=False, index=True)

    # Service information
    service_date = Column(DateTime, nullable=False)
    provider = Column(String, nullable=False)
    service_type = Column(String)  # e.g., "Full Service", "Regulation", "Battery Replacement"
    description = Column(Text)

    # Cost
    cost = Column(Numeric(10, 2))
    cost_currency = Column(String(3), default="USD")

    # Next service
    next_service_due = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    watch = relationship("Watch", back_populates="service_history")
    documents = relationship("ServiceDocument", back_populates="service", cascade="all, delete-orphan")


class ServiceDocument(Base):
    __tablename__ = "service_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_history_id = Column(UUID(as_uuid=True), ForeignKey("service_history.id", ondelete="CASCADE"), nullable=False, index=True)

    # File information
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    mime_type = Column(String, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    service = relationship("ServiceHistory", back_populates="documents")
