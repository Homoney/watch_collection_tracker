import uuid
from sqlalchemy import Column, String, Text, Numeric, DateTime, ForeignKey, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class ConditionEnum(str, enum.Enum):
    MINT = "mint"
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class Watch(Base):
    __tablename__ = "watches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id", ondelete="SET NULL"))
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="RESTRICT"), nullable=False)
    movement_type_id = Column(UUID(as_uuid=True), ForeignKey("movement_types.id", ondelete="RESTRICT"))

    # Basic information
    model = Column(String, nullable=False)
    reference_number = Column(String)
    serial_number = Column(String)

    # Purchase information
    purchase_date = Column(DateTime)
    retailer = Column(String)
    purchase_price = Column(Numeric(12, 2))
    purchase_currency = Column(String(3), default="USD")

    # Specifications
    case_diameter = Column(Numeric(5, 2))  # mm
    case_thickness = Column(Numeric(5, 2))  # mm
    lug_width = Column(Numeric(5, 2))  # mm
    water_resistance = Column(Integer)  # meters
    power_reserve = Column(Integer)  # hours

    # Complications (stored as JSON array of complication names)
    complications = Column(JSONB, default=[])

    # Condition
    condition = Column(
        Enum(ConditionEnum, values_callable=lambda x: [e.value for e in x])
    )

    # Market value tracking
    current_market_value = Column(Numeric(12, 2))
    current_market_currency = Column(String(3), default="USD")
    last_value_update = Column(DateTime)

    # Notes
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="watches")
    collection = relationship("Collection", back_populates="watches")
    brand = relationship("Brand", back_populates="watches")
    movement_type = relationship("MovementType", back_populates="watches")
    images = relationship("WatchImage", back_populates="watch", cascade="all, delete-orphan")
    service_history = relationship("ServiceHistory", back_populates="watch", cascade="all, delete-orphan")
    market_values = relationship("MarketValue", back_populates="watch", cascade="all, delete-orphan")
    accuracy_readings = relationship("MovementAccuracyReading", back_populates="watch", cascade="all, delete-orphan")
