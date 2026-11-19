"""Turn source text like "41.00 mm", "300.00 m", "~70 hours" into numbers,
and source words into this app's movement types and complications."""

import re
from decimal import Decimal, InvalidOperation
from typing import Iterable, List, Optional

_NUMBER = re.compile(r"(\d+(?:[.,]\d+)*)")


def _first_number(text) -> Optional[Decimal]:
    if text is None:
        return None
    m = _NUMBER.search(str(text))
    if not m:
        return None
    raw = m.group(1)
    # "28,800" is a thousands separator; "28,5" a decimal comma
    if re.fullmatch(r"\d{1,3}(,\d{3})+", raw):
        raw = raw.replace(",", "")
    else:
        raw = raw.replace(",", ".")
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def millimetres(text) -> Optional[Decimal]:
    value = _first_number(text)
    if value is None or value <= 0 or value >= 1000:
        return None
    return value.quantize(Decimal("0.01"))


def metres(text) -> Optional[int]:
    """Water resistance in metres; converts bar/atm (x10) and feet."""
    value = _first_number(text)
    if value is None or value <= 0:
        return None
    unit = str(text).lower()
    if "bar" in unit or "atm" in unit:
        value *= 10
    elif "ft" in unit or "feet" in unit:
        value = value * Decimal("0.3048")
    return int(value.to_integral_value())


def hours(text) -> Optional[int]:
    value = _first_number(text)
    if value is None or value <= 0:
        return None
    if "day" in str(text).lower():
        value *= 24
    return int(value.to_integral_value())


def integer(text) -> Optional[int]:
    value = _first_number(text)
    return int(value) if value is not None and value > 0 else None


# Movement type names seeded in the database (alembic 0001)
def movement_type(text) -> Optional[str]:
    t = (text or "").lower()
    if not t:
        return None
    if "spring drive" in t:
        return "Spring Drive"
    if "kinetic" in t:
        return "Kinetic"
    if "solar" in t or "eco-drive" in t:
        return "Solar"
    if "quartz" in t:
        return "Quartz"
    if "automatic" in t or "self-winding" in t:
        return "Automatic"
    if "manual" in t or "hand" in t:
        return "Hand-wound"
    return None


# Seeded complication names, matched against the source's function words
_COMPLICATION_WORDS = [
    ("Chronograph", ("chronograph",)),
    ("GMT", ("24 hour hand", "gmt")),
    ("Moon Phase", ("moon",)),
    ("Power Reserve Indicator", ("power reserve indicator", "power reserve display")),
    ("Small Seconds", ("small seconds", "sub seconds", "subsidiary seconds")),
    ("Tachymeter", ("tachymeter", "tachymetre")),
    ("Dive Bezel", ("0-60", "dive", "diver")),
    ("World Time", ("world time", "worldtime")),
    ("Perpetual Calendar", ("perpetual calendar",)),
    ("Annual Calendar", ("annual calendar",)),
    ("Tourbillon", ("tourbillon",)),
    ("Minute Repeater", ("minute repeater",)),
    ("Alarm", ("alarm",)),
]


def complications(texts: Iterable[Optional[str]]) -> List[str]:
    words = " | ".join(t for t in texts if t).lower()
    found = [
        name for name, keys in _COMPLICATION_WORDS if any(k in words for k in keys)
    ]
    if re.search(r"\bday\b", words) and "date" in words:
        found.append("Day-Date")
    elif re.search(r"\bdate\b", words):
        found.append("Date")
    return found


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


def norm_reference(text: str) -> str:
    """Compare references without case, spaces, dots or dashes."""
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())
