"""The WatchBase main photo of a watch, saved as a private "reference photo".

WatchBase does not license its photos (mostly brand press photos), so this
stays a private copy for the owner: one per watch, labelled, with its source
link, never replacing or outranking the owner's own photos, and left out of
PDF exports. Downloads go through the normal image pipeline (safe_fetch,
size cap, Pillow checks), at most one per second, with an honest User-Agent.

With a WatchBase key the photo comes from the Data Feed API's watch record.
Without one it comes from WatchBase's public site: its search, then the
watch page's og:image (see public.py).
"""

import logging
from typing import Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.watch import Watch
from app.models.watch_image import ImageSourceEnum, WatchImage
from app.spec_lookup import cache, http, keys, parse, public, service, watchbase
from app.utils import image_import, safe_fetch

logger = logging.getLogger(__name__)

throttle = http.Throttle(1.0)

NO_PHOTO = "No photo found for this watch; you can upload your own."
MESSAGES = {
    "saved": "Saved the reference photo from WatchBase.",
    "exists": "This watch already has a reference photo. Delete it to get it again.",
    "no_reference": "Add a reference number first, or upload your own photo.",
    "choices": "Several WatchBase watches match this reference. Enter the full "
    "reference (for example 5711/1A-010), pick yours with Look up on the Edit "
    "form, or upload your own photo.",
    "bad_key": service.MESSAGES["bad_key"],
    "unavailable": "WatchBase is not answering right now. Try again later, "
    "or upload your own photo.",
    "none": NO_PHOTO,
}


def _fetch(url, headers=None):
    throttle.wait()
    return safe_fetch.fetch_bytes(url, headers=headers)


def _resolve(db: Session, watch: Watch, watchbase_id: Optional[int], key: str):
    """(status, WatchBase watch dict or None)."""
    if watchbase_id is None:
        if not (watch.reference_number or "").strip():
            return "no_reference", None
        choices, tried = service._search(db, watch.reference_number, key)
        if not choices:
            return "none", None
        chosen = service._pick(choices, watch.reference_number, tried[-1])
        if chosen is None:
            return "choices", None
        watchbase_id = chosen["id"]
    return "ok", service._watch(db, watchbase_id, key)


def _from_api(db: Session, watch: Watch, watchbase_id: Optional[int], key: str):
    """(status, photo URLs, source page) from the Data Feed API."""
    status, w = _resolve(db, watch, watchbase_id, key)
    if status != "ok":
        return status, [], None
    return "ok", watchbase.photo_urls(w), watchbase.page_url(w)


def _site_search(db: Session, reference: str) -> list:
    norm = parse.norm_reference(reference)
    hit = cache.get(db, "watchbase-site-search", norm)
    if hit is None:
        hit = cache.get(db, "watchbase-site-search-empty", norm, max_age_days=1)
    if hit is not None:
        return hit
    found = public.search(reference, throttle)
    cache.put(
        db,
        "watchbase-site-search" if found else "watchbase-site-search-empty",
        norm,
        found,
    )
    return found


def _from_site(db: Session, watch: Watch):
    """(status, photo URLs, source page) from WatchBase's public pages."""
    reference = (watch.reference_number or "").strip()
    if not reference:
        return "no_reference", [], None
    found = _site_search(db, reference)
    if not found:
        return "none", [], None
    chosen = public.pick(found, reference)
    if chosen is None:
        return "choices", [], None
    return (
        "ok",
        public.photo_urls(chosen["url"], chosen["thumb"], throttle),
        chosen["url"],
    )


def save_reference_photo(
    db: Session, watch: Watch, watchbase_id: Optional[int] = None
) -> Tuple[str, Optional[WatchImage]]:
    """Returns (status, image). status is "saved" only when an image was stored."""
    exists = (
        db.query(WatchImage.id)
        .filter(
            WatchImage.watch_id == watch.id,
            WatchImage.source == ImageSourceEnum.REFERENCE_PHOTO,
        )
        .first()
    )
    if exists:
        return "exists", None
    key = keys.get_watchbase_key()
    try:
        if key:
            status, urls, source_url = _from_api(db, watch, watchbase_id, key)
        else:
            status, urls, source_url = _from_site(db, watch)
    except watchbase.BadKey:
        return "bad_key", None
    except watchbase.Unavailable:
        return "unavailable", None
    except Exception:
        logger.warning("Reference photo look-up failed", exc_info=True)
        return "unavailable", None
    if status != "ok":
        return status, None

    meta = None
    for url in urls:
        meta = image_import.save_image_from_url(
            url,
            str(watch.id),
            "reference",
            fetch=_fetch,
            headers={"User-Agent": http.USER_AGENT},
        )
        if meta:
            break
    if not meta:
        return "none", None

    has_images = (
        db.query(WatchImage.id).filter(WatchImage.watch_id == watch.id).first()
        is not None
    )
    max_order = (
        db.query(func.max(WatchImage.sort_order))
        .filter(WatchImage.watch_id == watch.id)
        .scalar()
    )
    image = WatchImage(
        watch_id=watch.id,
        **meta,
        is_primary=not has_images,  # never takes over from the owner's photos
        sort_order=(max_order + 1) if max_order is not None else 0,
        source=ImageSourceEnum.REFERENCE_PHOTO,
        source_url=source_url,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return "saved", image
