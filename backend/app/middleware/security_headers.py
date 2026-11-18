"""Security headers on every response (formerly set by nginx)."""

CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
    "frame-ancestors 'none'"
)

BASE_HEADERS = {
    "x-frame-options": "SAMEORIGIN",
    "x-content-type-options": "nosniff",
    "referrer-policy": "strict-origin-when-cross-origin",
    "permissions-policy": "geolocation=(), microphone=(), camera=()",
    "x-permitted-cross-domain-policies": "none",
}

# No CSP on uploaded files (it stops browsers' built-in PDF viewer) or on the
# API docs pages (they load their scripts from a CDN).
NO_CSP_PREFIXES = ("/uploads/", "/docs", "/redoc")


class SecurityHeadersMiddleware:
    """Pure ASGI middleware; a header the route already set is left alone."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        wanted = dict(BASE_HEADERS)
        if not path.startswith(NO_CSP_PREFIXES):
            wanted["content-security-policy"] = CSP

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                present = {name.decode("latin-1").lower() for name, _ in headers}
                for name, value in wanted.items():
                    if name not in present:
                        headers.append(
                            (name.encode("latin-1"), value.encode("latin-1"))
                        )
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)
