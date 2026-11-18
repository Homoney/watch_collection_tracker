"""One place for outgoing requests: honest User-Agent, short timeouts."""

import threading
import time
from typing import Optional

import httpx

USER_AGENT = (
    "WatchCollectionTracker/2 (self-hosted watch collection app; "
    "+https://github.com/Homoney/watch_collection_tracker)"
)

# Tests replace this with httpx.MockTransport; None = real network
TRANSPORT: Optional[httpx.BaseTransport] = None


def client(timeout: float = 15.0) -> httpx.Client:
    return httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
        transport=TRANSPORT,
    )


class Throttle:
    """At most one request per `interval` seconds, across threads."""

    def __init__(self, interval: float = 1.0, clock=time.monotonic, sleep=time.sleep):
        self.interval = interval
        self.clock = clock
        self.sleep = sleep
        self._lock = threading.Lock()
        self._last = -1e9

    def wait(self) -> None:
        with self._lock:
            delay = self._last + self.interval - self.clock()
            if delay > 0:
                self.sleep(delay)
            self._last = self.clock()
