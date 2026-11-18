"""In-memory rate limits per client address (formerly nginx limit_req).

Token buckets: `rate` requests per second refill, `burst` extra requests may
come at once. State lives in this process, so run a single app process.
Client addresses come from uvicorn, which honours X-Forwarded-For only from
TRUSTED_PROXIES.
"""

import json
import math
import re
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from app.config import settings


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: "re.Pattern[str]"
    rate: float  # tokens per second
    burst: int
    methods: Optional[Tuple[str, ...]] = None

    def matches(self, method: str, path: str) -> bool:
        if self.methods and method not in self.methods:
            return False
        return bool(self.pattern.match(path))


# First matching rule wins (same zones as the old nginx config)
RULES = (
    Rule("auth", re.compile(r"^/api/v1/auth/(login|register)$"), 5 / 60, 3),
    Rule(
        "account", re.compile(r"^/api/v1/auth/(change-password|refresh)$"), 10 / 60, 5
    ),
    Rule(
        "upload",
        re.compile(
            r"^/api/v1/watches/[^/]+/"
            r"(images|fetch-images|service-history/[^/]+/documents)$"
        ),
        10 / 60,
        10,
        methods=("POST",),
    ),
    Rule("api", re.compile(r"^/api/"), 10.0, 20),
)

MAX_KEYS = 10_000


class RateLimiter:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.buckets: Dict[Tuple[str, str], Tuple[float, float]] = {}

    def hit(self, rule: Rule, client: str) -> float:
        """Take one token. Returns 0 if allowed, else seconds to wait."""
        now = self.clock()
        capacity = rule.burst + 1
        key = (rule.name, client)
        tokens, last = self.buckets.get(key, (capacity, now))
        tokens = min(capacity, tokens + (now - last) * rule.rate)
        if tokens >= 1:
            self.buckets[key] = (tokens - 1, now)
            self._trim()
            return 0.0
        self.buckets[key] = (tokens, now)
        return (1 - tokens) / rule.rate

    def _trim(self):
        if len(self.buckets) > MAX_KEYS:
            # Drop the oldest half; a dropped client simply starts full again
            for key, _ in sorted(self.buckets.items(), key=lambda kv: kv[1][1])[
                : MAX_KEYS // 2
            ]:
                del self.buckets[key]


class RateLimitMiddleware:
    def __init__(self, app, limiter: Optional[RateLimiter] = None):
        self.app = app
        self.limiter = limiter or RateLimiter()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not settings.RATE_LIMIT_ENABLED:
            await self.app(scope, receive, send)
            return

        method, path = scope["method"], scope["path"]
        rule = next((r for r in RULES if r.matches(method, path)), None)
        if rule is not None:
            client = (scope.get("client") or ("unknown", 0))[0]
            wait = self.limiter.hit(rule, client)
            if wait > 0:
                body = json.dumps({"detail": "Too many requests"}).encode()
                await send(
                    {
                        "type": "http.response.start",
                        "status": 429,
                        "headers": [
                            (b"content-type", b"application/json"),
                            (b"retry-after", str(math.ceil(wait)).encode()),
                            (b"content-length", str(len(body)).encode()),
                        ],
                    }
                )
                await send({"type": "http.response.body", "body": body})
                return

        await self.app(scope, receive, send)
