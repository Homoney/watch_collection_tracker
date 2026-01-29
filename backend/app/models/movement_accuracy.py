import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class MovementAccuracyReading(Base):
    """
    Tracks watch movement accuracy by recording the watch's seconds position
    against an atomic clock reference at specific moments in time.

    Initial readings establish a baseline (watch is perfectly synced).
    Subsequent readings measure drift since the most recent initial reading.
    """

    __tablename__ = "movement_accuracy_readings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    watch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("watches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Reading data
    reference_time = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Atomic clock reference time when reading was taken",
    )
    watch_seconds_position = Column(
        Integer,
        nullable=False,
        comment="Watch second hand position when aligned: 0, 15, 30, or 45",
    )
    is_initial_reading = Column(
        Boolean,
        nullable=False,
        index=True,
        default=False,
        comment="True = baseline/reset point, False = drift measurement",
    )
    is_atomic_source = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="False if WorldTimeAPI failed and server time was used",
    )

    # Metadata
    notes = Column(Text, nullable=True, comment="User notes about this reading")
    timezone = Column(
        String(50), nullable=False, default="UTC", comment="Timezone used for display"
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    watch = relationship("Watch", back_populates="accuracy_readings")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "watch_seconds_position IN (0, 15, 30, 45)", name="valid_seconds_position"
        ),
    )

    def __repr__(self):
        return (
            f"<MovementAccuracyReading(id={self.id}, watch_id={self.watch_id}, "
            f"reference_time={self.reference_time}, position={self.watch_seconds_position}, "
            f"initial={self.is_initial_reading})>"
        )
