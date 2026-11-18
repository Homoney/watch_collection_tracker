"""Column types that behave the same on every database."""

import uuid
from datetime import timezone

from sqlalchemy import DateTime, Uuid
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator):
    """Timezone-aware datetime stored as UTC.

    SQLite has no timezone support and returns naive datetimes, so values are
    converted to UTC on the way in (naive values count as UTC) and marked as
    UTC on the way out.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value  # naive values are taken to be UTC already
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class GUID(TypeDecorator):
    """UUID column that also accepts UUID strings (as PostgreSQL did)."""

    impl = Uuid
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if isinstance(value, str):
            return uuid.UUID(value)
        return value
