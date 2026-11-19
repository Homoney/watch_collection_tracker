"""WatchBase's public site, used only to find a watch's main photo when no
WatchBase key is set.

Two requests per watch at most: the site's own search
(`/filter/results?q=<reference>`, allowed by robots.txt) and the watch page,
whose `og:image` tag names the main photo. Specs are never read from these
pages (that is what the licensed Data Feed API is for). Requests carry an
honest User-Agent and share the reference-photo throttle (1 per second).
"""

import html
import json
import re
from typing import List, Optional
from urllib.parse import urlencode, urlsplit

import httpx

from app.spec_lookup import http, parse
from app.spec_lookup.watchbase import PHOTO_HOSTS, SITE, Unavailable

SITE_HOST = "watchbase.com"

_BLOCK = re.compile(
    r'<a\s+href="(?P<url>[^"]+)"\s+class="[^"]*\bwatch-block\b[^"]*"[^>]*>(?P<body>.*?)</a>',
    re.S,
)
_REF = re.compile(r'class="bottomtext">\s*<strong>(?P<ref>[^<]+)</strong>', re.S)
_THUMB = re.compile(r'<img[^>]*\bdata-src="(?P<src>[^"]+)"', re.S)
_OG_IMAGE = re.compile(
    r'<meta\s+[^>]*property="og:image"[^>]*content="(?P<url>[^"]+)"', re.S
)


def _is_site_page(url: str) -> bool:
    parts = urlsplit(url)
    return parts.scheme == "https" and parts.hostname == SITE_HOST


def _is_photo(url: Optional[str]) -> bool:
    if not url:
        return False
    parts = urlsplit(url)
    return parts.scheme == "https" and parts.hostname in PHOTO_HOSTS


def _get(url: str, throttle) -> httpx.Response:
    throttle.wait()
    try:
        with http.client() as c:
            r = c.get(url)
    except httpx.HTTPError as exc:
        raise Unavailable(str(exc)) from exc
    if r.status_code >= 400:
        raise Unavailable(f"HTTP {r.status_code}")
    return r


def parse_search(text: str) -> List[dict]:
    """Watches in a /filter/results answer: url, reference, thumbnail."""
    try:
        data = json.loads(text)
    except ValueError:
        raise Unavailable("search answer is not JSON")
    found = []
    for m in _BLOCK.finditer(str(data.get("watchesHtml") or "")):
        url = html.unescape(m.group("url"))
        if not _is_site_page(url):
            continue
        ref = _REF.search(m.group("body"))
        thumb = _THUMB.search(m.group("body"))
        thumb_url = html.unescape(thumb.group("src")) if thumb else None
        found.append(
            {
                "url": url,
                "reference": html.unescape(ref.group("ref")).strip() if ref else "",
                "thumb": thumb_url if _is_photo(thumb_url) else None,
            }
        )
    return found


def search(reference: str, throttle) -> List[dict]:
    query = urlencode({"q": reference.strip()})
    return parse_search(_get(f"{SITE}/filter/results?{query}", throttle).text)


def pick(found: List[dict], reference: str) -> Optional[dict]:
    """One clear match: the only result, or the only exact reference match."""
    if len(found) == 1:
        return found[0]
    norm = parse.norm_reference(reference)
    exact = [
        f
        for f in found
        if parse.norm_reference(f["reference"]) == norm
        or parse.norm_reference(f["reference"].split("-")[0]) == norm
    ]
    return exact[0] if len(exact) == 1 else None


def og_image(page_html: str) -> Optional[str]:
    m = _OG_IMAGE.search(page_html)
    url = html.unescape(m.group("url")) if m else None
    return url if _is_photo(url) else None


def photo_urls(page_url: str, thumb: Optional[str], throttle) -> List[str]:
    """The page's og:image, then the search thumbnail at large and medium size."""
    urls = []
    if _is_site_page(page_url):
        image = og_image(_get(page_url, throttle).text)
        if image:
            urls.append(image)
    if thumb:
        large = thumb.replace("/watch/md/", "/watch/lg/", 1)
        urls += [u for u in (large, thumb) if u not in urls]
    return urls
