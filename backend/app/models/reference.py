import uuid
from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Brand(Base):
    __tablename__ = "brands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False, index=True)
    sort_order = Column(Integer, default=0)

    # Relationships
    watches = relationship("Watch", back_populates="brand")


class MovementType(Base):
    __tablename__ = "movement_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False, index=True)
    sort_order = Column(Integer, default=0)

    # Relationships
    watches = relationship("Watch", back_populates="movement_type")


class Complication(Base):
    __tablename__ = "complications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False, index=True)
    sort_order = Column(Integer, default=0)
