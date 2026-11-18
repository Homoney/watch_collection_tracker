import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.db_types import GUID


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

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
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
    # Bumped to invalidate every issued token (password change, logout, reset)
    token_version = Column(Integer, default=0, server_default="0", nullable=False)
    # Login throttling
    failed_login_count = Column(Integer, default=0, server_default="0", nullable=False)
    locked_until = Column(DateTime, nullable=True)
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
