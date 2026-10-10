"""UTC helpers for the legacy PostgreSQL timestamp schema."""
from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return a naive UTC value for existing timestamp-without-time-zone columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def as_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def as_utc_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
