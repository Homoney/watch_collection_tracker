import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class ImageSourceEnum(str, enum.Enum):
    USER_UPLOAD = "user_upload"
    GOOGLE_IMAGES = "google_images"
    URL_IMPORT = "url_import"


class WatchImage(Base):
    __tablename__ = "watch_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    watch_id = Column(UUID(as_uuid=True), ForeignKey("watches.id", ondelete="CASCADE"), nullable=False, index=True)

    # File information
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    mime_type = Column(String, nullable=False)

    # Image properties
    width = Column(Integer)
    height = Column(Integer)

    # Display properties
    is_primary = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    # Source tracking
    source = Column(Enum(ImageSourceEnum, values_callable=lambda x: [e.value for e in x]), default=ImageSourceEnum.USER_UPLOAD, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    watch = relationship("Watch", back_populates="images")
