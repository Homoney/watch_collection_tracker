"""grand-seiko.com: specs and the official photo for Grand Seiko references.

WatchBase lists only about 100 Grand Seiko watches (whole 2020 releases such
as SBGE253 are missing), so when it has no such watch we read the brand's
own page. Its robots.txt allows everything; its terms reserve copyright in
the texts and images. So: one page fetch per user click (cached), facts only
(numbers and short spec values), one private reference photo on request,
always with a link back to the page. Nothing is republished.

The page for a reference is /us-en/collections/<reference>g, e.g. sbge253g.
An unknown reference answers HTTP 200 with a "404 Page Not Found" heading,
so a page counts only when its heading is the reference asked for.
"""

import logging
import re
from decimal import Decimal
from typing import List, Optional
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup

from app.spec_lookup import cache, http, parse

logger = logging.getLogger(__name__)

SITE = "https://www.grand-seiko.com"
HOST = "www.grand-seiko.com"
SOURCE_NAME = "grand-seiko.com"
BRAND = "Grand Seiko"

throttle = http.Throttle(1.0)

# SBGE253, SLGH005, SBGA211 ...; the site adds a "g" (sbge253g)
_REF = re.compile(r"^(s[a-z]g[a-z]\d{3})g?$")
_DIAMETER = re.compile(r"diameter\s*([\d.,]+)\s*mm", re.I)
_THICKNESS = re.compile(r"thickness\s*([\d.,]+)\s*mm", re.I)
_JEWELS = re.compile(r"(\d+)\s*jewels", re.I)


class Unavailable(Exception):
    """The site could not be reached or answered with an error."""


def model_code(reference: str) -> Optional[str]:
    """ "SBGE253", "sbge-253", "SBGE253G" -> "sbge253"; None if not a GS form."""
    m = _REF.match(parse.norm_reference(reference))
    return m.group(1) if m else None


def applies(brand: Optional[str], reference: str) -> bool:
    """Grand Seiko, or (no brand / Seiko, under which older GS were sold) a
    reference in Grand Seiko's form."""
    b = (brand or "").strip().lower()
    if b and b not in ("grand seiko", "seiko"):
        return False
    return model_code(reference) is not None


def page_url(code: str) -> str:
    return f"{SITE}/us-en/collections/{code}g"


def _value(td) -> str:
    return " ".join(td.get_text(" ").split())


def _photo(soup) -> Optional[str]:
    tag = soup.find("meta", attrs={"property": "og:image"})
    url = urljoin(SITE, (tag.get("content") or "").strip()) if tag else ""
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname != HOST:
        return None
    if "/collections/products/" not in parts.path.lower():
        return None  # the site logo, not a product photo
    return url


def parse_page(html: str, code: str) -> Optional[dict]:
    """{"fields", "movement", "photo"} or None when it is not this watch's page."""
    soup = BeautifulSoup(html, "lxml")
    heading = soup.find("h1")
    if heading is None or model_code(heading.get_text(" ", strip=True)) != code:
        return None
    collection = soup.select_one(".productMain-data ._collection")
    fields: dict = {
        "brand_name": BRAND,
        "model": " ".join(collection.get_text(" ").split()) if collection else None,
    }
    movement: dict = {}
    features: List[str] = []
    for row in soup.find_all("tr"):
        th, td = row.find("th"), row.find("td")
        if th is None or td is None:
            continue
        label = " ".join(th.get_text(" ").split()).lower().rstrip(":")
        value = _value(td)
        if not value:
            continue
        if label == "caliber no.":
            link = td.find("a")
            fields["caliber"] = (
                link.get_text(" ", strip=True) if link else value.split()[0]
            )
        elif label == "movement type":
            fields["movement_type_name"] = parse.movement_type(value)
        elif label == "power reserve":
            # "Approx. 72 hours(3 days)": the hours, not the days in brackets
            fields["power_reserve"] = parse.hours(value.split("(")[0])
        elif label == "water resistance":
            fields["water_resistance"] = parse.metres(value)
        elif label == "glass material":
            fields["crystal"] = value
        elif label in ("exterior", "case material"):
            fields["case_material"] = value
        elif label == "case size":
            d, t = _DIAMETER.search(value), _THICKNESS.search(value)
            fields["case_diameter"] = parse.millimetres(d.group(1)) if d else None
            fields["case_thickness"] = parse.millimetres(t.group(1)) if t else None
        elif label == "band width":
            fields["lug_width"] = parse.millimetres(value)
        elif label.startswith("other details"):
            features = [
                " ".join(li.get_text(" ").split()) for li in td.find_all("li")
            ] or [value]
    for text in features:
        m = _JEWELS.search(text)
        if m:
            movement["jewels"] = int(m.group(1))
    # "24-hour hand" is the GMT hand; the word lists use spaces
    fields["complications"] = parse.complications(
        [t.replace("-", " ") for t in features]
    )
    # Stored as JSON in the cache: millimetres as numbers, like the API sends
    fields = {
        k: float(v) if isinstance(v, Decimal) else v
        for k, v in fields.items()
        if v not in (None, "", [])
    }
    movement.update(
        {
            "caliber": fields.get("caliber"),
            "caliber_brand": BRAND,
            "power_reserve": fields.get("power_reserve"),
        }
    )
    return {
        "fields": fields,
        "movement": {k: v for k, v in movement.items() if v},
        "photo": _photo(soup),
    }


def _fetch(url: str) -> Optional[str]:
    """Page text; None for a missing page; Unavailable when down."""
    throttle.wait()
    try:
        with http.client() as c:
            r = c.get(url)
    except httpx.HTTPError as exc:
        raise Unavailable(type(exc).__name__) from exc
    if r.status_code == 404:
        return None
    if r.status_code != 200 or urlsplit(str(r.url)).hostname != HOST:
        raise Unavailable(f"HTTP {r.status_code}")
    return r.text


def lookup(db, reference: str) -> Optional[dict]:
    """{"url", "fields", "movement", "photo"} or None (no page, or site down).

    Found pages are cached like other answers; "no page" for a day, so a new
    release shows up soon; a site that is down is not remembered.
    """
    code = model_code(reference)
    if not code:
        return None
    hit = cache.get(db, "grandseiko", code)
    if hit is None:
        hit = cache.get(db, "grandseiko-empty", code, max_age_days=1)
    if hit is not None:
        return hit or None
    url = page_url(code)
    try:
        html = _fetch(url)
    except Unavailable as exc:
        logger.info("grand-seiko.com unavailable: %s", exc)
        return None
    page = parse_page(html, code) if html else None
    if not page:
        cache.put(db, "grandseiko-empty", code, {})
        return None
    page["url"] = url
    cache.put(db, "grandseiko", code, page)
    return page
