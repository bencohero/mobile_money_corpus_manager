import hashlib
import hmac
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from .config import settings


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self._events = defaultdict(deque)
        self._lock = threading.Lock()

    def _key(self, request: Request, scope: str) -> str:
        address = request.client.host if request.client else "unknown"
        return hmac.new(
            settings.jwt_secret.encode("utf-8"), f"{scope}:{address}".encode("utf-8"), hashlib.sha256
        ).hexdigest()

    def check(self, request: Request, scope: str, *, record: bool = True) -> None:
        fingerprint = self._key(request, scope)
        now = time.monotonic()
        with self._lock:
            events = self._events[fingerprint]
            while events and events[0] <= now - self.window_seconds:
                events.popleft()
            if len(events) >= self.limit:
                raise HTTPException(429, "Trop de tentatives. Réessayez plus tard.", headers={"Retry-After": str(self.window_seconds)})
            if record:
                events.append(now)

    def record(self, request: Request, scope: str) -> None:
        self.check(request, scope, record=True)


registration_limiter = SlidingWindowLimiter(60, 600)
login_limiter = SlidingWindowLimiter(10, 300)
