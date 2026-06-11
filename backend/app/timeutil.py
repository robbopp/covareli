from datetime import datetime, timezone


def to_naive_utc(dt: datetime) -> datetime:
    """Normalize any datetime to naive UTC (project-wide convention)."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
