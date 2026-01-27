import uuid
from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class CurrencyEnum(str, enum.Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CHF = "CHF"


class ThemeEnum(str, enum.Enum):
    LIGHT = "light"
    DARK = "dark"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    default_currency = Column(Enum(CurrencyEnum), default=CurrencyEnum.USD, nullable=False)
    theme = Column(Enum(ThemeEnum), default=ThemeEnum.LIGHT, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    collections = relationship("Collection", back_populates="user", cascade="all, delete-orphan")
    watches = relationship("Watch", back_populates="user", cascade="all, delete-orphan")
