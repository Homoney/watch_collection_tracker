import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class CurrencyEnum(enum.Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CHF = "CHF"


class ThemeEnum(enum.Enum):
    light = "light"
    dark = "dark"


class UserRole(enum.Enum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x], name="userrole"),
        default=UserRole.user,
        nullable=False,
    )
    default_currency = Column(
        Enum(CurrencyEnum, name="currencyenum"),
        default=CurrencyEnum.USD,
        nullable=False,
    )
    theme = Column(
        Enum(ThemeEnum, name="themeenum"), default=ThemeEnum.light, nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    collections = relationship(
        "Collection", back_populates="user", cascade="all, delete-orphan"
    )
    watches = relationship("Watch", back_populates="user", cascade="all, delete-orphan")
    saved_searches = relationship(
        "SavedSearch", back_populates="user", cascade="all, delete-orphan"
    )
