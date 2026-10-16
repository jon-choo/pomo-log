"""Timer start/stop, Pomodoro cycling and manual entry."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path

import db
from timeutil import SGT, UTC, sgt_date, utc_now

ACTIVE_TIMER_KEY = "active_timer"
DEFAULT_WORK_MINUTES = 25
DEFAULT_BREAK_MINUTES = 5
MAX_MANUAL_MINUTES = 24 * 60


# Pomodoro length settings

def get_pomodoro_lengths(db_path: Path = db.DEFAULT_DB_PATH) -> tuple[int, int]:
    """Work and break minutes."""
    work = db.get_setting("pomodoro_work_minutes", str(DEFAULT_WORK_MINUTES), db_path=db_path)
    brk = db.get_setting("pomodoro_break_minutes", str(DEFAULT_BREAK_MINUTES), db_path=db_path)
    return int(work), int(brk)


def set_pomodoro_lengths(
    work_minutes: int, break_minutes: int, db_path: Path = db.DEFAULT_DB_PATH
) -> None:
    if work_minutes < 1 or break_minutes < 1:
        raise ValueError("Work and break lengths must be at least 1 minute")
    db.set_setting("pomodoro_work_minutes", str(work_minutes), db_path=db_path)
    db.set_setting("pomodoro_break_minutes", str(break_minutes), db_path=db_path)


# Timer state

@dataclass
class TimerState:
    subject_id: int
    mode: str  # 'pomodoro' | 'freeform'
    started_at: datetime
    work_seconds: int = 0
    break_seconds: int = 0
    logged_intervals: int = 0

    def to_json(self) -> str:
        data = asdict(self)
        data["started_at"] = self.started_at.isoformat()
        return json.dumps(data)

    @classmethod
    def from_json(cls, raw: str) -> "TimerState":
        data = json.loads(raw)
        data["started_at"] = datetime.fromisoformat(data["started_at"])
        return cls(**data)


def _save(state: TimerState, db_path: Path) -> None:
    db.set_setting(ACTIVE_TIMER_KEY, state.to_json(), db_path=db_path)


def get_active_timer(db_path: Path = db.DEFAULT_DB_PATH) -> TimerState | None:
    raw = db.get_setting(ACTIVE_TIMER_KEY, db_path=db_path)
    return TimerState.from_json(raw) if raw is not None else None


def phase_info(state: TimerState, now: datetime | None = None) -> dict:
    """Current phase, elapsed and remaining time."""
    now = now if now is not None else utc_now()
    elapsed = max(0, int((now - state.started_at).total_seconds()))

    if state.mode == "freeform":
        return {
            "phase": "free",
            "elapsed_seconds": elapsed,
            "phase_elapsed_seconds": elapsed,
            "phase_remaining_seconds": None,
            "completed_work_intervals": 0,
        }

    cycle = state.work_seconds + state.break_seconds
    full_cycles, into_cycle = divmod(elapsed, cycle)
    if into_cycle < state.work_seconds:
        return {
            "phase": "work",
            "elapsed_seconds": elapsed,
            "phase_elapsed_seconds": into_cycle,
            "phase_remaining_seconds": state.work_seconds - into_cycle,
            "completed_work_intervals": full_cycles,
        }
    return {
        "phase": "break",
        "elapsed_seconds": elapsed,
        "phase_elapsed_seconds": into_cycle - state.work_seconds,
        "phase_remaining_seconds": cycle - into_cycle,
        "completed_work_intervals": full_cycles + 1,
    }


def _work_interval_bounds(state: TimerState, index: int) -> tuple[datetime, datetime]:
    cycle = state.work_seconds + state.break_seconds
    start = state.started_at + timedelta(seconds=index * cycle)
    return start, start + timedelta(seconds=state.work_seconds)


# Start / tick / stop

def start_timer(
    subject_id: int,
    mode: str,
    now: datetime | None = None,
    db_path: Path = db.DEFAULT_DB_PATH,
) -> TimerState:
    if mode not in ("pomodoro", "freeform"):
        raise ValueError(f"Invalid timer mode '{mode}'")
    if get_active_timer(db_path) is not None:
        raise ValueError("A timer is already running")
    subject = db.get_subject(subject_id, db_path=db_path)
    if subject is None:
        raise ValueError(f"No subject with id {subject_id}")
    if subject["archived"]:
        raise ValueError(f"Subject '{subject['name']}' is archived")

    state = TimerState(
        subject_id=subject_id,
        mode=mode,
        started_at=now if now is not None else utc_now(),
    )
    if mode == "pomodoro":
        work_minutes, break_minutes = get_pomodoro_lengths(db_path)
        state.work_seconds = work_minutes * 60
        state.break_seconds = break_minutes * 60
    _save(state, db_path)
    return state


def _log_completed_intervals(state: TimerState, now: datetime, db_path: Path) -> list[int]:
    """Log finished work intervals that aren't logged yet."""
    if state.mode != "pomodoro":
        return []
    completed = phase_info(state, now)["completed_work_intervals"]
    ids = []
    for index in range(state.logged_intervals, completed):
        start, end = _work_interval_bounds(state, index)
        ids.append(db.log_session(state.subject_id, start, end, "pomodoro", db_path=db_path))
        state.logged_intervals = index + 1
        _save(state, db_path)
    return ids


def tick(now: datetime | None = None, db_path: Path = db.DEFAULT_DB_PATH) -> list[int]:
    """Log intervals finished since the last call."""
    state = get_active_timer(db_path)
    if state is None:
        return []
    return _log_completed_intervals(state, now if now is not None else utc_now(), db_path)


def stop_timer(now: datetime | None = None, db_path: Path = db.DEFAULT_DB_PATH) -> list[int]:
    """Stop the timer, log what's owed, clear it."""
    now = now if now is not None else utc_now()
    state = get_active_timer(db_path)
    if state is None:
        raise ValueError("No timer is running")

    ids = _log_completed_intervals(state, now, db_path)

    if state.mode == "freeform":
        if now > state.started_at:
            ids.append(db.log_session(state.subject_id, state.started_at, now, "freeform", db_path=db_path))
    else:
        info = phase_info(state, now)
        if info["phase"] == "work":
            partial_start, _ = _work_interval_bounds(state, info["completed_work_intervals"])
            if now > partial_start:
                ids.append(db.log_session(state.subject_id, partial_start, now, "pomodoro", db_path=db_path))

    db.delete_setting(ACTIVE_TIMER_KEY, db_path=db_path)
    return ids


# Manual entry

def log_manual_session(
    subject_id: int,
    day: date,
    duration_minutes: int,
    today: date | None = None,
    db_path: Path = db.DEFAULT_DB_PATH,
) -> int:
    """Log a session by date and duration, anchored at 00:00 SGT."""
    if duration_minutes < 1:
        raise ValueError("Duration must be at least 1 minute")
    if duration_minutes > MAX_MANUAL_MINUTES:
        raise ValueError("Duration cannot exceed 24 hours")
    if day > (today if today is not None else sgt_date()):
        raise ValueError("Cannot log a session on a future date")

    start = datetime.combine(day, time.min, tzinfo=SGT).astimezone(UTC)
    end = start + timedelta(minutes=duration_minutes)
    return db.log_session(subject_id, start, end, "manual", db_path=db_path)
