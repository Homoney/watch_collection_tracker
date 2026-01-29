import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ValueSourceEnum(str, enum.Enum):
    MANUAL = "manual"
    CHRONO24 = "chrono24"
    API = "api"


class MarketValue(Base):
    __tablename__ = "market_values"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    watch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("watches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Value information
    value = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    # Source tracking
    source = Column(
        Enum(ValueSourceEnum, values_callable=lambda x: [e.value for e in x]),
        default=ValueSourceEnum.MANUAL,
        nullable=False,
    )
    notes = Column(Text)

    # Timestamp
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    watch = relationship("Watch", back_populates="market_values")
