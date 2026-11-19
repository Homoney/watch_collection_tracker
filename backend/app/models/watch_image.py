import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.db_types import GUID


class ImageSourceEnum(str, enum.Enum):
    USER_UPLOAD = "user_upload"
    GOOGLE_IMAGES = "google_images"
    URL_IMPORT = "url_import"
    REFERENCE_PHOTO = "reference_photo"  # catalogue photo (WatchBase), private copy


class WatchImage(Base):
    __tablename__ = "watch_images"
    __table_args__ = (
        # At most one primary image per watch (#206)
        Index(
            "uq_watch_images_one_primary",
            "watch_id",
            unique=True,
            sqlite_where=text("is_primary = 1"),
            postgresql_where=text("is_primary"),
        ),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    watch_id = Column(
        GUID,
        ForeignKey("watches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # File information
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    mime_type = Column(String, nullable=False)

    # Image properties
    width = Column(Integer)
    height = Column(Integer)

    # Display properties
    is_primary = Column(Boolean, default=False, index=True)
    sort_order = Column(Integer, default=0)

    # Source tracking
    source = Column(
        Enum(ImageSourceEnum, values_callable=lambda x: [e.value for e in x]),
        default=ImageSourceEnum.USER_UPLOAD,
        nullable=False,
    )
    # Page the photo came from, for photos not taken by the owner
    source_url = Column(String(500))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    watch = relationship("Watch", back_populates="images")
