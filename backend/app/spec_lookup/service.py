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
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.spec_lookup import (
    cache,
    calibercorner,
    grandseiko,
    keys,
    links,
    parse,
    watchbase,
)

logger = logging.getLogger(__name__)

MESSAGES = {
    "links_only": "Automatic look-up is off (no WatchBase key). Use the links "
    "to look the reference up yourself.",
    "not_found": "WatchBase has no watch with this reference. Check it, or "
    "use the links.",
    "bad_key": "WatchBase did not accept the API key (wrong key or no credits "
    "left). An admin can change it on the Admin page.",
    "unavailable": "WatchBase could not be reached or answered with an error, "
    "so the reference was not checked. Try again later, or use the links.",
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
        # Where the photo offered with has_photo comes from: {"name"}
        "photo_source": None,
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


def _from_brand_site(
    db, reference: str, brand: Optional[str], caliber: Optional[str], why: str
) -> Optional[dict]:
    """An "ok" answer from the brand's own page when WatchBase gave none."""
    if not grandseiko.applies(brand, reference):
        return None
    try:
        page = grandseiko.lookup(db, reference)
    except Exception:  # a parser surprise must not break the look-up
        logger.warning("grand-seiko.com look-up failed", exc_info=True)
        page = None
    if not page:
        return None
    fields = page["fields"]
    source = {"name": grandseiko.SOURCE_NAME, "url": page["url"]}
    answer = _answer(
        "ok",
        reference,
        brand or grandseiko.BRAND,
        message=f"{why} Filled the empty fields from {grandseiko.SOURCE_NAME}. "
        "Check them before saving.",
        fields=dict(fields),
        sources={name: source for name in fields},
        movement=dict(page["movement"], source=source) if page["movement"] else None,
        has_photo=bool(page.get("photo")),
        photo_source={"name": grandseiko.SOURCE_NAME} if page.get("photo") else None,
    )
    _add_movement_facts(db, answer, grandseiko.BRAND, fields.get("caliber") or caliber)
    return answer


def _search(db: Session, reference: str, key: str) -> Tuple[list, List[str]]:
    """Search each form of the reference until one finds watches.

    Cached by the exact query sent (any case): "SBGE 225" finding nothing
    must not hide what "SBGE225" finds.
    """
    tried = []
    for query in watchbase.queries(reference):
        tried.append(query)
        qkey = query.lower()
        hit = cache.get(db, "watchbase-refnr", qkey)
        if hit is None:
            hit = cache.get(db, "watchbase-refnr-empty", qkey, max_age_days=1)
        if hit is None:
            hit = watchbase.search(query, key)
            cache.put(
                db, "watchbase-refnr" if hit else "watchbase-refnr-empty", qkey, hit
            )
        if hit:
            return hit, tried
    return [], tried


def _watch(db: Session, watch_id: int, key: str) -> dict:
    hit = cache.get(db, "watchbase-watch", str(watch_id))
    if hit is not None:
        return hit
    w = watchbase.watch(watch_id, key)
    cache.put(db, "watchbase-watch", str(watch_id), w)
    return w


def _pick(choices: list, reference: str, query: str = "") -> Optional[dict]:
    """One clear match: the only result, or the only exact reference match."""
    if len(choices) == 1:
        return choices[0]
    norms = {parse.norm_reference(reference), parse.norm_reference(query)} - {""}
    exact = [
        c
        for c in choices
        if parse.norm_reference(c["reference"]) in norms
        or parse.norm_reference(c["reference"].split("-")[0]) in norms
    ]
    return exact[0] if len(exact) == 1 else None


def _not_found(tried: List[str]) -> str:
    searched = ", ".join(f'"{q}"' for q in tried)
    return (
        f"WatchBase has no watch with this reference (searched for {searched}). "
        "Check the reference, or use the links."
    )


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
        found = _from_brand_site(
            db, reference, brand, caliber, "Automatic WatchBase look-up is off."
        )
        if found:
            return found
        answer = _answer("links_only", reference, brand)
        _add_movement_facts(db, answer, brand, caliber)
        return answer
    try:
        if watchbase_id is None:
            choices, tried = _search(db, reference, key)
            if not choices:
                # WatchBase has no such watch: try the brand's own site
                found = _from_brand_site(
                    db,
                    reference,
                    brand,
                    caliber,
                    "WatchBase has no watch with this reference.",
                )
                if found:
                    return found
                # The calibre may still be known
                answer = _answer(
                    "not_found", reference, brand, message=_not_found(tried)
                )
                _add_movement_facts(db, answer, brand, caliber)
                return answer
            chosen = _pick(choices, reference, tried[-1])
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
        photo_source=(
            {"name": watchbase.SOURCE_NAME} if watchbase.has_photo(w) else None
        ),
    )
    _add_movement_facts(
        db,
        answer,
        movement.get("caliber_brand") or fields.get("brand_name") or brand,
        fields.get("caliber") or caliber,
    )
    return answer
