"""WatchBase Data Feed API (https://watchbase.com/manuals/datafeed).

search/refnr is a "contains" search by reference; the Watch call returns all
fields and is the one WatchBase charges for (US $0.30 each), so its answers
are cached. The key goes in the POST body, never in a URL, so it cannot end
up in a log line.
"""

import logging
from typing import Dict, List, Tuple
from urllib.parse import urlsplit

import httpx

from app.spec_lookup import http, parse

logger = logging.getLogger(__name__)

API = "https://api.watchbase.com/v1"
SITE = "https://watchbase.com"
SOURCE_NAME = "WatchBase"
# Photos are only taken from WatchBase's own image server
PHOTO_HOSTS = {"cdn.watchbase.com"}


class BadKey(Exception):
    pass


class Unavailable(Exception):
    pass


def _call(path: str, key: str, params: Dict[str, str]) -> dict:
    data = {"key": key, "format": "json", **params}
    try:
        with http.client() as c:
            r = c.post(f"{API}/{path}", data=data)
    except httpx.HTTPError as exc:
        raise Unavailable(type(exc).__name__) from None
    if r.status_code in (401, 403):
        raise BadKey()
    if r.status_code != 200:
        raise Unavailable(f"HTTP {r.status_code}")
    try:
        body = r.json()
    except ValueError:
        raise Unavailable("not JSON") from None
    if not isinstance(body, dict):
        raise Unavailable("unexpected answer")
    error = body.get("error") or (body.get("response") or {}).get("error")
    if error:
        if "key" in str(error).lower() or "credit" in str(error).lower():
            raise BadKey()
        raise Unavailable("API error")
    return body.get("response", body)


def _as_list(value) -> list:
    """XML-to-JSON style answers wrap lists: {"watch": [...]} or one dict."""
    if value is None:
        return []
    if isinstance(value, dict):
        inner = value.get("watch", value)
        return inner if isinstance(inner, list) else [inner]
    return list(value)


def search(reference: str, key: str) -> List[dict]:
    body = _call("search/refnr", key, {"q": reference})
    choices = []
    for w in _as_list(body.get("watches")):
        if not isinstance(w, dict) or not w.get("id"):
            continue
        choices.append(
            {
                "id": int(w["id"]),
                "reference": w.get("refnr") or w.get("reference_number") or "",
                "name": w.get("name") or "",
                "brand": (w.get("brand") or {}).get("name") or "",
                "family": (w.get("family") or {}).get("name") or "",
            }
        )
    return choices


def watch(watch_id: int, key: str) -> dict:
    body = _call("watch", key, {"id": str(int(watch_id))})
    w = body.get("watch")
    if not isinstance(w, dict):
        raise Unavailable("no watch in answer")
    return w


def page_url(w: dict) -> str:
    brand = (w.get("brand") or {}).get("slug")
    family = (w.get("family") or {}).get("slug")
    ref = parse.slug(w.get("reference_number") or "")
    if brand and family and ref:
        return f"{SITE}/{brand}/{family}/{ref}"
    return SITE


def to_fields(w: dict) -> Tuple[dict, dict]:
    """Form fields from a Watch answer, plus movement facts for display."""
    case = w.get("case") or {}
    cal = w.get("caliber") or {}
    materials = case.get("materials")
    if isinstance(materials, dict):
        materials = materials.get("material")
    if isinstance(materials, str):
        materials = [materials]
    fields = {
        "brand_name": (w.get("brand") or {}).get("name"),
        "model": w.get("name"),
        "movement_type_name": parse.movement_type(cal.get("type")),
        "case_diameter": parse.millimetres(case.get("diameter")),
        "case_thickness": parse.millimetres(case.get("height")),
        "lug_width": parse.millimetres(case.get("lugwidth")),
        "water_resistance": parse.metres(w.get("waterresistance")),
        "power_reserve": parse.hours(cal.get("powerreserve")),
        "caliber": (
            (str(cal.get("reference_number")).strip() or None)
            if cal.get("reference_number")
            else None
        ),
        "crystal": case.get("glass") or None,
        "case_material": ", ".join(m for m in (materials or []) if m) or None,
        "complications": parse.complications(
            [
                cal.get("hands"),
                cal.get("chronograph"),
                cal.get("additional"),
                (
                    cal.get("display")
                    if "date" in str(cal.get("display", "")).lower()
                    else None
                ),
                case.get("bezel"),
            ]
        ),
    }
    fields = {k: v for k, v in fields.items() if v not in (None, "", [])}
    movement = {
        "caliber": fields.get("caliber"),
        "caliber_brand": cal.get("brand"),
        "jewels": parse.integer(cal.get("jewels")),
        "frequency": cal.get("frequency") or None,
        "power_reserve": fields.get("power_reserve"),
    }
    return fields, {k: v for k, v in movement.items() if v}


def photo_urls(w: dict) -> list:
    """Candidate URLs for the main photo, large size first, WatchBase CDN only."""
    images = w.get("images") or []
    if isinstance(images, dict):
        images = images.get("image") or []
    if isinstance(images, str):
        images = [images]
    urls = []
    for url in images[:1]:
        if not isinstance(url, str) or urlsplit(url).hostname not in PHOTO_HOSTS:
            continue
        if urlsplit(url).scheme != "https":
            continue
        if "/watch/md/" in url:
            urls.append(url.replace("/watch/md/", "/watch/lg/", 1))
        urls.append(url)
    return urls


def has_photo(w: dict) -> bool:
    return bool(photo_urls(w))
