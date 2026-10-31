"""Singapore-time day and week boundaries."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

SGT = ZoneInfo("Asia/Singapore")
UTC = ZoneInfo("UTC")


def utc_now() -> datetime:
    """Current time, UTC."""
    return datetime.now(UTC)


def to_sgt(dt: datetime) -> datetime:
    """Convert an aware datetime to SGT."""
    if dt.tzinfo is None:
        raise ValueError("to_sgt requires an aware datetime, got a naive one")
    return dt.astimezone(SGT)


def sgt_date(dt: datetime | None = None) -> date:
    """SGT calendar date of an instant."""
    moment = dt if dt is not None else utc_now()
    return to_sgt(moment).date()


def week_start_date(d: date) -> date:
    """Sunday that starts the week containing d."""
    days_since_sunday = (d.weekday() + 1) % 7  # Mon=0 .. Sun=6
    return d - timedelta(days=days_since_sunday)


def day_bounds_utc(d: date) -> tuple[datetime, datetime]:
    """UTC bounds of an SGT day."""
    start_sgt = datetime.combine(d, time.min, tzinfo=SGT)
    end_sgt = start_sgt + timedelta(days=1)
    return start_sgt.astimezone(UTC), end_sgt.astimezone(UTC)


def week_bounds_utc(d: date) -> tuple[datetime, datetime]:
    """UTC bounds of an SGT week."""
    start_sgt = datetime.combine(week_start_date(d), time.min, tzinfo=SGT)
    end_sgt = start_sgt + timedelta(days=7)
    return start_sgt.astimezone(UTC), end_sgt.astimezone(UTC)
