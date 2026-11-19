"""Search links the user can open by hand. Nothing is fetched by the server."""

from typing import List, Optional
from urllib.parse import quote_plus

# Official sites of seeded brands, for a site search on the brand's own pages
BRAND_SITES = {
    "rolex": "rolex.com",
    "omega": "omegawatches.com",
    "seiko": "seikowatches.com",
    "grand seiko": "grand-seiko.com",
    "tudor": "tudorwatch.com",
    "cartier": "cartier.com",
    "patek philippe": "patek.com",
    "audemars piguet": "audemarspiguet.com",
    "iwc": "iwc.com",
    "jaeger-lecoultre": "jaeger-lecoultre.com",
    "breitling": "breitling.com",
    "tag heuer": "tagheuer.com",
    "longines": "longines.com",
    "tissot": "tissotwatches.com",
    "hamilton": "hamiltonwatch.com",
    "oris": "oris.ch",
    "panerai": "panerai.com",
    "zenith": "zenith-watches.com",
    "blancpain": "blancpain.com",
    "citizen": "citizenwatch.com",
    "casio": "casio.com",
    "sinn": "sinn.de",
    "nomos": "nomos-glashuette.com",
}

_SEARCH = "https://duckduckgo.com/?q="


def build(
    reference: str, brand: Optional[str], caliber_page: Optional[str] = None
) -> List[dict]:
    ref = (reference or "").strip()
    brand = (brand or "").strip()
    words = f"{brand} {ref}".strip()
    links = [
        {
            "label": "WatchBase",
            "url": f"{_SEARCH}{quote_plus('site:watchbase.com ' + words)}",
        },
        {
            "label": "Caliber Corner",
            "url": caliber_page
            or f"{_SEARCH}{quote_plus('site:calibercorner.com ' + words)}",
        },
    ]
    site = BRAND_SITES.get(brand.lower())
    if site:
        links.append(
            {
                "label": f"{brand} website",
                "url": f"{_SEARCH}{quote_plus(f'site:{site} {ref}')}",
            }
        )
    elif brand:
        links.append(
            {
                "label": f"{brand} website",
                "url": f"{_SEARCH}{quote_plus(f'{brand} official {ref}')}",
            }
        )
    return links
