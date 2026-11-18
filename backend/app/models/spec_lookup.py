import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, String, UniqueConstraint

from app.database import Base
from app.db_types import GUID


class SpecLookupCache(Base):
    """Answers from the spec sources, kept so a repeat look-up costs nothing.

    `source` is the provider ("watchbase-search", "watchbase-watch",
    "calibercorner"); `lookup_key` is the normalised reference, watch id or
    caliber. Shared by all users: the data is public catalogue data.
    """

    __tablename__ = "spec_lookup_cache"
    __table_args__ = (UniqueConstraint("source", "lookup_key"),)

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    source = Column(String(40), nullable=False)
    lookup_key = Column(String(200), nullable=False)
    data = Column(JSON, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)
