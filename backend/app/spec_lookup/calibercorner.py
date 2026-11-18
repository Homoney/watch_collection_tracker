"""Caliber Corner (https://calibercorner.com): movement facts by caliber.

Its terms allow personal, non-commercial use and ask for credit; its
robots.txt allows the caliber pages and the sitemaps but not its search. So
we never search: we find the caliber page through an index built from the
post sitemaps (refreshed weekly, kept in DATA_DIR/cache), fetch at most one
page per second, read only the facts from the spec table, and show a link
back. Pages are cached in the database like every other answer.
"""

import json
import logging
import os
import re
import time
from typing import Dict, Optional, Tuple

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.spec_lookup import cache, http, parse

logger = logging.getLogger(__name__)

SITE = "https://calibercorner.com"
SITEMAPS = (f"{SITE}/post-sitemap.xml", f"{SITE}/post-sitemap2.xml")
SOURCE_NAME = "Caliber Corner"
INDEX_MAX_AGE = 7 * 24 * 3600
INDEX_RETRY_AFTER = 3600  # after a failed or empty fetch, wait before trying again

throttle = http.Throttle(1.0)

# The live sitemaps wrap each URL in CDATA: <loc><![CDATA[https://...]]></loc>
_LOC = re.compile(r"<loc>\s*(?:<!\[CDATA\[)?\s*([^<\s\]]+)\s*(?:\]\]>)?\s*</loc>")
_PAGE = re.compile(r"^https://calibercorner\.com/([a-z0-9-]+?)-caliber-([a-z0-9-]+)/?$")
# Brand slugs Caliber Corner uses for a brand under another name
_BRAND_ALIASES = {
    "grand-seiko": ("grand-seiko", "seiko"),
    "seiko": ("seiko", "seiko-sii", "s-epson"),
}


def _index_file() -> str:
    return os.path.join(settings.DATA_DIR, "cache", "calibercorner-index.json")


def _get(url: str) -> Optional[str]:
    throttle.wait()
    try:
        with http.client() as c:
            r = c.get(url)
    except httpx.HTTPError as exc:
        logger.info("Caliber Corner unreachable (%s)", type(exc).__name__)
        return None
    if r.status_code != 200:
        logger.info("Caliber Corner answered HTTP %s for %s", r.status_code, url)
        return None
    return r.text


def build_index(sitemaps) -> Dict[str, str]:
    """{"<brand-slug>|<caliber>": page URL} from sitemap XML texts."""
    index = {}
    for xml in sitemaps:
        for loc in _LOC.findall(xml or ""):
            m = _PAGE.match(loc)
            if m:
                index[f"{m.group(1)}|{parse.norm_reference(m.group(2))}"] = loc
    return index


def _save_index(path: str, data: dict) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            json.dump(data, fh)
    except OSError:
        logger.warning("Could not save the Caliber Corner index", exc_info=True)


def load_index() -> Dict[str, str]:
    """The sitemap index, refreshed weekly. A failed or empty fetch is not
    retried for an hour, so look-ups do not refetch the sitemaps each time."""
    path = _index_file()
    stored: dict = {}
    try:
        with open(path) as fh:
            stored = json.load(fh)
    except (OSError, ValueError):
        pass
    index = stored.get("index") or {}
    now = time.time()
    if index and now - stored.get("fetched_at", 0) < INDEX_MAX_AGE:
        return index
    if now - stored.get("failed_at", 0) < INDEX_RETRY_AFTER:
        return index  # tried recently: keep what we have (maybe nothing)
    texts = [_get(u) for u in SITEMAPS]
    fresh = build_index(texts) if any(texts) else {}
    if not fresh:
        # Source down or format not understood: keep the old index, retry later
        if any(texts):
            logger.warning("Caliber Corner sitemaps had no caliber pages")
        _save_index(path, {**stored, "index": index, "failed_at": now})
        return index
    _save_index(path, {"fetched_at": now, "index": fresh})
    return fresh


def find_page(index: Dict[str, str], brand: str, caliber: str) -> Optional[str]:
    """Exact caliber first, then the closest prefix match (2824 -> 2824-2)."""
    number = parse.norm_reference(caliber)
    if not number:
        return None
    brand_slug = parse.slug(brand)
    slugs = _BRAND_ALIASES.get(brand_slug, (brand_slug,))
    for s in slugs:
        if f"{s}|{number}" in index:
            return index[f"{s}|{number}"]
    best: Optional[Tuple[int, str]] = None
    for s in slugs:
        prefix = f"{s}|"
        for key, url in index.items():
            if not key.startswith(prefix):
                continue
            other = key[len(prefix) :]
            if other.startswith(number) or number.startswith(other):
                gap = abs(len(other) - len(number))
                if best is None or gap < best[0]:
                    best = (gap, url)
    return best[1] if best else None


_LABELS = {
    "power reserve": ("power_reserve", parse.hours),
    "jewels": ("jewels", parse.integer),
    "vibrations per hour": ("frequency", lambda t: t),
    "frequency": ("frequency", lambda t: t),
    "beat rate": ("frequency", lambda t: t),
    "diameter": ("diameter", parse.millimetres),
    "movement type": ("movement_type", lambda t: t),
}


def parse_page(html: str) -> dict:
    """Facts from the label/value spec table; nothing else from the page."""
    soup = BeautifulSoup(html, "lxml")
    facts = {}
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) != 2:
            continue
        label = " ".join(cells[0].get_text(" ").split()).lower().rstrip(":?")
        value = " ".join(cells[1].get_text(" ").split())
        if label in _LABELS and value:
            name, convert = _LABELS[label]
            converted = convert(value)
            if converted and name not in facts:
                facts[name] = converted
    if "frequency" in facts:
        facts["frequency"] = facts["frequency"].replace(" ,", ",").strip()
    if "diameter" in facts:
        facts["diameter"] = str(facts["diameter"])
    return facts


def caliber_facts(db, brand: str, caliber: str) -> Optional[dict]:
    """{"url", "power_reserve", "jewels", "frequency", ...} or None."""
    if not brand or not caliber:
        return None
    cache_key = f"{parse.slug(brand)}|{parse.norm_reference(caliber)}"
    hit = cache.get(db, "calibercorner", cache_key)
    if hit is not None:
        return hit or None
    index = load_index()
    if not index:
        return None  # no index yet (source down): do not remember "no page"
    url = find_page(index, brand, caliber)
    if not url:
        cache.put(db, "calibercorner", cache_key, {})  # remember "no page"
        return None
    html = _get(url)
    if html is None:
        return None  # down: do not cache, try again next time
    facts = parse_page(html)
    facts["url"] = url
    cache.put(db, "calibercorner", cache_key, facts)
    return facts
