"""The look-up the API calls. Always returns an answer, never raises.

status:
  ok          fields to fill (and where each came from)
  choices     several watches match; ask the user, then call again with one
  not_found   the source has no watch for this reference
  links_only  no WatchBase key: links to look it up by hand
  bad_key     WatchBase refused the key (wrong, expired or out of credits)
  unavailable a source is down or answered something unexpected
Every answer has `links`, so the user always has a next step.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.spec_lookup import cache, calibercorner, keys, links, parse, watchbase

logger = logging.getLogger(__name__)

MESSAGES = {
    "links_only": "Automatic look-up is off (no WatchBase key). Use the links "
    "to look the reference up yourself.",
    "not_found": "No watch found for this reference. Check it, or use the links.",
    "bad_key": "WatchBase did not accept the API key (wrong key or no credits "
    "left). An admin can change it on the Admin page.",
    "unavailable": "The look-up service is not answering right now. Try again "
    "later, or use the links.",
    "choices": "Several watches match. Pick yours.",
    "ok": "Filled the empty fields we found. Check them before saving.",
}


def _answer(status, reference, brand, **extra) -> dict:
    caliber_page = (extra.get("movement") or {}).get("url")
    answer = {
        "status": status,
        "message": MESSAGES[status],
        "reference": reference,
        "fields": {},
        "sources": {},
        "choices": [],
        "movement": None,
        "links": links.build(reference, brand, caliber_page),
        # The matched WatchBase watch, and whether it has a photo to save
        "watchbase_id": None,
        "has_photo": False,
    }
    answer.update(extra)
    return answer


def _add_movement_facts(db, answer: dict, brand: Optional[str], caliber: Optional[str]):
    """Caliber Corner facts; fills power reserve only when WatchBase had none."""
    try:
        facts = calibercorner.caliber_facts(db, brand, caliber)
    except Exception:  # a parser surprise must not break the look-up
        logger.warning("Caliber Corner look-up failed", exc_info=True)
        facts = None
    if not facts:
        return
    source = {"name": calibercorner.SOURCE_NAME, "url": facts["url"]}
    movement = dict(answer.get("movement") or {})
    movement.update({k: v for k, v in facts.items() if k != "url"})
    movement["caliber"] = movement.get("caliber") or caliber
    movement["source"] = source
    answer["movement"] = movement
    if facts.get("power_reserve") and "power_reserve" not in answer["fields"]:
        answer["fields"]["power_reserve"] = facts["power_reserve"]
        answer["sources"]["power_reserve"] = source
    answer["links"] = links.build(answer["reference"], brand, facts["url"])


def _search(db: Session, reference: str, key: str) -> list:
    norm = parse.norm_reference(reference)
    hit = cache.get(db, "watchbase-search", norm)
    if hit is None:
        hit = cache.get(db, "watchbase-search-empty", norm, max_age_days=1)
    if hit is not None:
        return hit
    choices = watchbase.search(reference, key)
    cache.put(
        db, "watchbase-search" if choices else "watchbase-search-empty", norm, choices
    )
    return choices


def _watch(db: Session, watch_id: int, key: str) -> dict:
    hit = cache.get(db, "watchbase-watch", str(watch_id))
    if hit is not None:
        return hit
    w = watchbase.watch(watch_id, key)
    cache.put(db, "watchbase-watch", str(watch_id), w)
    return w


def _pick(choices: list, reference: str) -> Optional[dict]:
    """One clear match: the only result, or the only exact reference match."""
    if len(choices) == 1:
        return choices[0]
    norm = parse.norm_reference(reference)
    exact = [
        c
        for c in choices
        if parse.norm_reference(c["reference"]) == norm
        or parse.norm_reference(c["reference"]).split("-")[0] == norm
    ]
    return exact[0] if len(exact) == 1 else None


def lookup(
    db: Session,
    reference: str,
    brand: Optional[str] = None,
    caliber: Optional[str] = None,
    watchbase_id: Optional[int] = None,
) -> dict:
    reference = (reference or "").strip()
    key = keys.get_watchbase_key()
    if not key:
        answer = _answer("links_only", reference, brand)
        _add_movement_facts(db, answer, brand, caliber)
        return answer
    try:
        if watchbase_id is None:
            choices = _search(db, reference, key)
            if not choices:
                return _answer("not_found", reference, brand)
            chosen = _pick(choices, reference)
            if chosen is None:
                return _answer("choices", reference, brand, choices=choices[:25])
            watchbase_id = chosen["id"]
        w = _watch(db, watchbase_id, key)
    except watchbase.BadKey:
        return _answer("bad_key", reference, brand)
    except watchbase.Unavailable as exc:
        logger.info("WatchBase unavailable: %s", exc)
        return _answer("unavailable", reference, brand)
    except Exception:
        logger.warning("WatchBase look-up failed", exc_info=True)
        return _answer("unavailable", reference, brand)

    fields, movement = watchbase.to_fields(w)
    source = {"name": watchbase.SOURCE_NAME, "url": watchbase.page_url(w)}
    answer = _answer(
        "ok",
        reference,
        brand or fields.get("brand_name"),
        fields=fields,
        sources={name: source for name in fields},
        movement=dict(movement, source=source) if movement else None,
        watchbase_id=watchbase_id,
        has_photo=watchbase.has_photo(w),
    )
    _add_movement_facts(
        db,
        answer,
        movement.get("caliber_brand") or fields.get("brand_name") or brand,
        fields.get("caliber") or caliber,
    )
    return answer
