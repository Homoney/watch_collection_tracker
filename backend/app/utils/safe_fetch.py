"""Download remote images without reaching internal addresses.

Rules for every request (including each redirect hop):
- only http and https, only ports 80 and 443
- the host must resolve only to public (global) IP addresses
- the connection goes to the IP that was checked, so a second DNS answer
  cannot swap in an internal address
- the body is streamed and abandoned once it passes max_bytes
"""

import ipaddress
import socket
from typing import Callable, List, Optional
from urllib.parse import urljoin, urlsplit

import httpx

DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_MAX_REDIRECTS = 3
ALLOWED_SCHEMES = {"http": 80, "https": 443}

Resolver = Callable[[str, int], List[str]]


class UnsafeURLError(ValueError):
    """The URL points somewhere the server must not fetch."""


class DownloadTooLargeError(ValueError):
    """The response body is larger than allowed."""


def _system_resolver(host: str, port: int) -> List[str]:
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    return list({info[4][0] for info in infos})


def _is_public(ip: str) -> bool:
    addr = ipaddress.ip_address(ip.split("%", 1)[0])
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped:
        addr = addr.ipv4_mapped
    return addr.is_global and not addr.is_multicast


def check_url(url: str, resolver: Resolver = _system_resolver) -> tuple:
    """Validate a URL. Returns (scheme, host, port, ip) or raises UnsafeURLError."""
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as exc:
        raise UnsafeURLError("Malformed URL") from exc
    scheme = (parts.scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        raise UnsafeURLError("Only http and https URLs are allowed")
    host = parts.hostname
    if not host:
        raise UnsafeURLError("URL has no host")
    if parts.username or parts.password:
        raise UnsafeURLError("Credentials in URLs are not allowed")
    port = port or ALLOWED_SCHEMES[scheme]
    if port not in (80, 443):
        raise UnsafeURLError("Only ports 80 and 443 are allowed")
    try:
        ips = resolver(host, port)
    except (OSError, UnicodeError) as exc:
        raise UnsafeURLError("Host does not resolve") from exc
    if not ips or not all(_is_public(ip) for ip in ips):
        raise UnsafeURLError("Host resolves to a non-public address")
    return scheme, host, port, ips[0]


def fetch_bytes(
    url: str,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
    timeout: float = 30.0,
    headers: Optional[dict] = None,
    resolver: Resolver = _system_resolver,
    transport: Optional[httpx.BaseTransport] = None,
) -> tuple:
    """GET a public URL. Returns (content_type, body_bytes)."""
    with httpx.Client(
        timeout=timeout, follow_redirects=False, transport=transport
    ) as client:
        for _ in range(max_redirects + 1):
            scheme, host, port, ip = check_url(url, resolver)
            parts = urlsplit(url)
            ip_host = f"[{ip}]" if ":" in ip else ip
            target = f"{scheme}://{ip_host}:{port}{parts.path or '/'}"
            if parts.query:
                target += f"?{parts.query}"
            req_headers = dict(headers or {})
            default_port = ALLOWED_SCHEMES[scheme]
            req_headers["Host"] = host if port == default_port else f"{host}:{port}"
            request = client.build_request(
                "GET",
                target,
                headers=req_headers,
                extensions={"sni_hostname": host} if scheme == "https" else {},
            )
            response = client.send(request, stream=True)
            try:
                if response.is_redirect:
                    location = response.headers.get("location")
                    if not location:
                        raise UnsafeURLError("Redirect without a location")
                    url = urljoin(url, location)
                    continue
                response.raise_for_status()
                declared = response.headers.get("content-length")
                if declared and declared.isdigit() and int(declared) > max_bytes:
                    raise DownloadTooLargeError("Response is too large")
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > max_bytes:
                        raise DownloadTooLargeError("Response is too large")
                return response.headers.get("content-type", ""), bytes(body)
            finally:
                response.close()
    raise UnsafeURLError("Too many redirects")
