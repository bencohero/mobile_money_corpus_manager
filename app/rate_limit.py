import hashlib
import hmac
import logging
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .config import settings
from .time_utils import utc_now

logger = logging.getLogger("mobile_money_corpus.rate_limit")


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
                logger.warning("rate limit exceeded scope=%s", scope)
                raise HTTPException(429, "Trop de tentatives. Réessayez plus tard.", headers={"Retry-After": str(self.window_seconds)})
            if record:
                events.append(now)
            if len(self._events) > 10000:
                for key in list(self._events):
                    if not self._events[key] or self._events[key][-1] <= now - self.window_seconds:
                        del self._events[key]
                while len(self._events) > 10000:
                    self._events.pop(next(iter(self._events)))

    def record(self, request: Request, scope: str) -> None:
        self.check(request, scope, record=True)


class SharedRateLimiter(SlidingWindowLimiter):
    """PostgreSQL-backed fixed windows, with a bounded per-process fallback.

    The database bucket is an atomic upsert, so all workers and replicas share
    the same counter.  Expired rows are removed opportunistically.  Before
    migration 0008 (or during a database outage), the inherited in-memory
    limiter remains active rather than silently disabling protection.
    """

    def check(self, request: Request, scope: str, *, db=None, record: bool = True) -> None:
        if db is None:
            return super().check(request, scope, record=True)
        fingerprint = self._key(request, scope)
        try:
            if not record:
                row = db.execute(text("""
                    SELECT event_count, expires_at FROM rate_limit_buckets
                    WHERE bucket_key=:key AND scope=:scope AND expires_at > CURRENT_TIMESTAMP
                """), {"key": fingerprint, "scope": scope}).one_or_none()
                if row and row.event_count >= self.limit:
                    logger.warning("shared rate limit exceeded scope=%s", scope)
                    retry_after = max(1, int((row.expires_at - utc_now()).total_seconds()))
                    raise HTTPException(429, "Trop de tentatives. Réessayez plus tard.", headers={"Retry-After": str(retry_after)})
                return
            row = db.execute(text("""
                INSERT INTO rate_limit_buckets
                    (bucket_key, scope, window_started_at, event_count, expires_at)
                VALUES (:key, :scope, CURRENT_TIMESTAMP, 1,
                        CURRENT_TIMESTAMP + (:window * INTERVAL '1 second'))
                ON CONFLICT (bucket_key, scope) DO UPDATE SET
                    window_started_at = CASE
                        WHEN rate_limit_buckets.expires_at <= CURRENT_TIMESTAMP THEN CURRENT_TIMESTAMP
                        ELSE rate_limit_buckets.window_started_at END,
                    event_count = CASE
                        WHEN rate_limit_buckets.expires_at <= CURRENT_TIMESTAMP THEN 1
                        ELSE rate_limit_buckets.event_count + 1 END,
                    expires_at = CASE
                        WHEN rate_limit_buckets.expires_at <= CURRENT_TIMESTAMP
                        THEN CURRENT_TIMESTAMP + (:window * INTERVAL '1 second')
                        ELSE rate_limit_buckets.expires_at END
                RETURNING event_count, expires_at
            """), {"key": fingerprint, "scope": scope, "window": self.window_seconds}).one()
            db.commit()
            if row.event_count > self.limit:
                logger.warning("shared rate limit exceeded scope=%s", scope)
                retry_after = max(1, int((row.expires_at - utc_now()).total_seconds()))
                raise HTTPException(429, "Trop de tentatives. Réessayez plus tard.", headers={"Retry-After": str(retry_after)})
            db.execute(text("DELETE FROM rate_limit_buckets WHERE expires_at <= CURRENT_TIMESTAMP"))
            db.commit()
        except HTTPException:
            raise
        except SQLAlchemyError:
            db.rollback()
            super().check(request, scope, record=True)

    def record(self, request: Request, scope: str, *, db=None) -> None:
        self.check(request, scope, db=db, record=True)


registration_limiter = SharedRateLimiter(60, 600)
login_limiter = SharedRateLimiter(10, 300)
workshop_language_limiter = SharedRateLimiter(20, 600)
