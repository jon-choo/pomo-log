"""Logic layer: session calculations built on top of db.py + timeutil.py.

Nothing here touches sqlite directly - it composes db.py's query functions
and does the aggregation/grouping that doesn't belong in the data layer.
All "today"/"this week" boundaries come from timeutil, so they stay in SGT
regardless of what timezone the app happens to run in.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import db
from timeutil import day_bounds_utc, sgt_date, week_bounds_utc, week_start_date


# ---------------------------------------------------------------------------
# Totals
# ---------------------------------------------------------------------------

def total_seconds(
    start: datetime | None = None,
    end: datetime | None = None,
    subject_id: int | None = None,
    category_id: int | None = None,
    db_path: Path = db.DEFAULT_DB_PATH,
) -> int:
    sessions = db.list_sessions(
        start=start, end=end, subject_id=subject_id, category_id=category_id, db_path=db_path
    )
    return sum(s["duration_seconds"] for s in sessions)


def today_total(d: date | None = None, db_path: Path = db.DEFAULT_DB_PATH) -> int:
    d = d if d is not None else sgt_date()
    start, end = day_bounds_utc(d)
    return total_seconds(start=start, end=end, db_path=db_path)


def week_total(d: date | None = None, db_path: Path = db.DEFAULT_DB_PATH) -> int:
    d = d if d is not None else sgt_date()
    start, end = week_bounds_utc(d)
    return total_seconds(start=start, end=end, db_path=db_path)


def all_time_total(db_path: Path = db.DEFAULT_DB_PATH) -> int:
    return total_seconds(db_path=db_path)


# ---------------------------------------------------------------------------
# Breakdowns
# ---------------------------------------------------------------------------

def _subject_lookup(db_path: Path) -> dict[int, dict]:
    return {s["id"]: s for s in db.list_subjects(include_archived=True, db_path=db_path)}


def _category_lookup(db_path: Path) -> dict[int, dict]:
    return {c["id"]: c for c in db.list_categories(include_archived=True, db_path=db_path)}


def breakdown_by_subject(
    start: datetime | None = None, end: datetime | None = None, db_path: Path = db.DEFAULT_DB_PATH
) -> list[dict]:
    """Total seconds per subject, busiest first. Looks up archived
    subjects/categories too, since a past session can reference either."""
    sessions = db.list_sessions(start=start, end=end, db_path=db_path)
    subjects = _subject_lookup(db_path)
    categories = _category_lookup(db_path)

    totals: dict[int, int] = {}
    for s in sessions:
        totals[s["subject_id"]] = totals.get(s["subject_id"], 0) + s["duration_seconds"]

    rows = []
    for subject_id, seconds in totals.items():
        subject = subjects[subject_id]
        rows.append(
            {
                "subject_id": subject_id,
                "subject_name": subject["name"],
                "category_id": subject["category_id"],
                "category_name": categories[subject["category_id"]]["name"],
                "total_seconds": seconds,
            }
        )
    rows.sort(key=lambda row: row["total_seconds"], reverse=True)
    return rows


def breakdown_by_category(
    start: datetime | None = None, end: datetime | None = None, db_path: Path = db.DEFAULT_DB_PATH
) -> list[dict]:
    """Total seconds per category, busiest first."""
    sessions = db.list_sessions(start=start, end=end, db_path=db_path)
    categories = _category_lookup(db_path)

    totals: dict[int, int] = {}
    for s in sessions:
        totals[s["category_id"]] = totals.get(s["category_id"], 0) + s["duration_seconds"]

    rows = [
        {
            "category_id": category_id,
            "category_name": categories[category_id]["name"],
            "total_seconds": seconds,
        }
        for category_id, seconds in totals.items()
    ]
    rows.sort(key=lambda row: row["total_seconds"], reverse=True)
    return rows


# ---------------------------------------------------------------------------
# Charts / history
# ---------------------------------------------------------------------------

def daily_series(d: date | None = None, db_path: Path = db.DEFAULT_DB_PATH) -> list[dict]:
    """Per-day totals (seconds) for the SGT week containing d, Sunday first."""
    d = d if d is not None else sgt_date()
    start_of_week = week_start_date(d)
    series = []
    for offset in range(7):
        day = start_of_week + timedelta(days=offset)
        start, end = day_bounds_utc(day)
        series.append({"date": day, "total_seconds": total_seconds(start=start, end=end, db_path=db_path)})
    return series


def list_weeks_with_data(db_path: Path = db.DEFAULT_DB_PATH) -> list[date]:
    """SGT week-start (Sunday) dates for every week with at least one
    logged session, newest first - the options for a past-week picker."""
    sessions = db.list_sessions(db_path=db_path)
    weeks = {
        week_start_date(sgt_date(datetime.fromisoformat(s["start_time"]))) for s in sessions
    }
    return sorted(weeks, reverse=True)


# ---------------------------------------------------------------------------
# Streak
# ---------------------------------------------------------------------------

def current_streak(d: date | None = None, db_path: Path = db.DEFAULT_DB_PATH) -> int:
    """Consecutive SGT days, ending at d (default today), with >=1 session.
    If d itself has no session yet, it's skipped rather than breaking the
    streak - so logging nothing /yet/ today doesn't zero out yesterday's
    streak, but a day fully missed still breaks it."""
    d = d if d is not None else sgt_date()
    sessions = db.list_sessions(db_path=db_path)
    days_with_sessions = {sgt_date(datetime.fromisoformat(s["start_time"])) for s in sessions}

    day = d if d in days_with_sessions else d - timedelta(days=1)
    streak = 0
    while day in days_with_sessions:
        streak += 1
        day -= timedelta(days=1)
    return streak


# ---------------------------------------------------------------------------
# Weekly goal
# ---------------------------------------------------------------------------

def weekly_goal_progress(d: date | None = None, db_path: Path = db.DEFAULT_DB_PATH) -> dict:
    """Progress toward the configured weekly goal, or goal_minutes=None if
    none has been set. percent is capped at 100."""
    goal_raw = db.get_setting("weekly_goal_minutes", db_path=db_path)
    goal_minutes = int(goal_raw) if goal_raw is not None else None
    actual_seconds = week_total(d, db_path=db_path)

    percent = None
    if goal_minutes:
        percent = min(100.0, (actual_seconds / 60 / goal_minutes) * 100)

    return {
        "goal_minutes": goal_minutes,
        "actual_seconds": actual_seconds,
        "percent": percent,
    }
