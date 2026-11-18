"""Look-up answers cached in the database, so a repeat look-up is free."""

from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.spec_lookup import SpecLookupCache


def get(db: Session, source: str, key: str, max_age_days: Optional[int] = None) -> Any:
    days = settings.SPEC_LOOKUP_CACHE_DAYS if max_age_days is None else max_age_days
    row = (
        db.query(SpecLookupCache)
        .filter(SpecLookupCache.source == source, SpecLookupCache.lookup_key == key)
        .first()
    )
    if row is None or row.fetched_at < datetime.utcnow() - timedelta(days=days):
        return None
    return row.data


def put(db: Session, source: str, key: str, data: Any) -> None:
    row = (
        db.query(SpecLookupCache)
        .filter(SpecLookupCache.source == source, SpecLookupCache.lookup_key == key)
        .first()
    )
    if row is None:
        row = SpecLookupCache(source=source, lookup_key=key)
        db.add(row)
    row.data = data
    row.fetched_at = datetime.utcnow()
    db.commit()
