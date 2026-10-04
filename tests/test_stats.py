from datetime import date, timedelta

import pytest

import db
import stats
from timeutil import day_bounds_utc, week_bounds_utc


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    db.init_db(path)
    return path


@pytest.fixture
def setup(db_path):
    """Two categories, two subjects, matching the sample plan (SAT Math
    under School, IT Module under Work)."""
    school = db.create_category("School", db_path=db_path)
    work = db.create_category("Work", db_path=db_path)
    sat_math = db.create_subject("SAT Math", school, db_path=db_path)
    it_module = db.create_subject("IT Module", work, db_path=db_path)
    return {
        "db_path": db_path,
        "school": school,
        "work": work,
        "sat_math": sat_math,
        "it_module": it_module,
    }


def log(setup, subject_id, day: date, minutes: int, mode="manual"):
    start, _ = day_bounds_utc(day)
    start = start + timedelta(hours=9)  # mid-morning SGT, comfortably inside the day
    end = start + timedelta(minutes=minutes)
    return db.log_session(subject_id, start, end, mode=mode, db_path=setup["db_path"])


# ---------------------------------------------------------------------------
# Totals
# ---------------------------------------------------------------------------

def test_today_total_only_counts_today(setup):
    today = date(2026, 10, 4)  # a Sunday
    log(setup, setup["sat_math"], today, 25)
    log(setup, setup["sat_math"], today - timedelta(days=1), 50)

    assert stats.today_total(today, db_path=setup["db_path"]) == 25 * 60


def test_week_total_sums_whole_week(setup):
    sunday = date(2026, 10, 4)
    log(setup, setup["sat_math"], sunday, 25)
    log(setup, setup["sat_math"], sunday + timedelta(days=3), 25)  # Wednesday, same week
    log(setup, setup["sat_math"], sunday - timedelta(days=1), 25)  # Saturday, previous week

    assert stats.week_total(sunday, db_path=setup["db_path"]) == 50 * 60


def test_all_time_total_ignores_week_boundaries(setup):
    log(setup, setup["sat_math"], date(2026, 1, 1), 10)
    log(setup, setup["sat_math"], date(2026, 10, 4), 20)

    assert stats.all_time_total(db_path=setup["db_path"]) == 30 * 60


# ---------------------------------------------------------------------------
# Breakdowns
# ---------------------------------------------------------------------------

def test_breakdown_by_subject_sums_and_sorts_busiest_first(setup):
    today = date(2026, 10, 4)
    log(setup, setup["sat_math"], today, 10)
    log(setup, setup["it_module"], today, 30)

    rows = stats.breakdown_by_subject(db_path=setup["db_path"])
    assert [r["subject_name"] for r in rows] == ["IT Module", "SAT Math"]
    assert rows[0]["total_seconds"] == 30 * 60
    assert rows[0]["category_name"] == "Work"


def test_breakdown_by_category_groups_subjects_under_same_category(setup):
    other_math = db.create_subject("SAT English", setup["school"], db_path=setup["db_path"])
    today = date(2026, 10, 4)
    log(setup, setup["sat_math"], today, 10)
    log(setup, other_math, today, 15)
    log(setup, setup["it_module"], today, 5)

    rows = stats.breakdown_by_category(db_path=setup["db_path"])
    by_name = {r["category_name"]: r["total_seconds"] for r in rows}
    assert by_name["School"] == 25 * 60
    assert by_name["Work"] == 5 * 60


def test_breakdown_resolves_archived_subject_and_category(setup):
    today = date(2026, 10, 4)
    log(setup, setup["sat_math"], today, 10)
    db.archive_subject(setup["sat_math"], db_path=setup["db_path"])
    db.archive_category(setup["school"], db_path=setup["db_path"])

    rows = stats.breakdown_by_subject(db_path=setup["db_path"])
    assert rows[0]["subject_name"] == "SAT Math"
    assert rows[0]["category_name"] == "School"


def test_breakdown_respects_time_range(setup):
    sunday = date(2026, 10, 4)
    log(setup, setup["sat_math"], sunday, 10)
    log(setup, setup["sat_math"], sunday - timedelta(days=7), 99)

    start, end = week_bounds_utc(sunday)
    rows = stats.breakdown_by_subject(start=start, end=end, db_path=setup["db_path"])
    assert len(rows) == 1
    assert rows[0]["total_seconds"] == 10 * 60


# ---------------------------------------------------------------------------
# Daily series / week history
# ---------------------------------------------------------------------------

def test_daily_series_has_seven_days_starting_sunday(setup):
    sunday = date(2026, 10, 4)
    log(setup, setup["sat_math"], sunday, 10)
    log(setup, setup["sat_math"], sunday + timedelta(days=2), 20)  # Tuesday

    series = stats.daily_series(sunday, db_path=setup["db_path"])
    assert len(series) == 7
    assert series[0]["date"] == sunday
    assert series[0]["total_seconds"] == 10 * 60
    assert series[2]["total_seconds"] == 20 * 60
    assert series[1]["total_seconds"] == 0


def test_daily_series_same_regardless_of_which_day_in_week_is_passed(setup):
    sunday = date(2026, 10, 4)
    log(setup, setup["sat_math"], sunday, 10)

    from_sunday = stats.daily_series(sunday, db_path=setup["db_path"])
    from_saturday = stats.daily_series(sunday + timedelta(days=6), db_path=setup["db_path"])
    assert from_sunday == from_saturday


def test_list_weeks_with_data(setup):
    log(setup, setup["sat_math"], date(2026, 10, 4), 10)  # week of Oct 4
    log(setup, setup["sat_math"], date(2026, 9, 20), 10)  # week of Sep 20

    weeks = stats.list_weeks_with_data(db_path=setup["db_path"])
    assert weeks == [date(2026, 10, 4), date(2026, 9, 20)]


def test_list_weeks_with_data_empty_when_no_sessions(setup):
    assert stats.list_weeks_with_data(db_path=setup["db_path"]) == []


# ---------------------------------------------------------------------------
# Streak
# ---------------------------------------------------------------------------

def test_streak_zero_with_no_sessions(setup):
    assert stats.current_streak(date(2026, 10, 4), db_path=setup["db_path"]) == 0


def test_streak_counts_consecutive_days(setup):
    today = date(2026, 10, 4)
    for offset in range(3):
        log(setup, setup["sat_math"], today - timedelta(days=offset), 5)

    assert stats.current_streak(today, db_path=setup["db_path"]) == 3


def test_streak_not_broken_by_missing_today(setup):
    today = date(2026, 10, 4)
    log(setup, setup["sat_math"], today - timedelta(days=1), 5)
    log(setup, setup["sat_math"], today - timedelta(days=2), 5)
    # nothing logged for `today` yet

    assert stats.current_streak(today, db_path=setup["db_path"]) == 2


def test_streak_broken_by_a_fully_missed_day(setup):
    today = date(2026, 10, 4)
    log(setup, setup["sat_math"], today, 5)
    log(setup, setup["sat_math"], today - timedelta(days=2), 5)  # gap on today-1

    assert stats.current_streak(today, db_path=setup["db_path"]) == 1


# ---------------------------------------------------------------------------
# Weekly goal
# ---------------------------------------------------------------------------

def test_weekly_goal_progress_with_no_goal_set(setup):
    result = stats.weekly_goal_progress(date(2026, 10, 4), db_path=setup["db_path"])
    assert result["goal_minutes"] is None
    assert result["percent"] is None


def test_weekly_goal_progress_computes_percent(setup):
    db.set_setting("weekly_goal_minutes", "60", db_path=setup["db_path"])
    log(setup, setup["sat_math"], date(2026, 10, 4), 30)

    result = stats.weekly_goal_progress(date(2026, 10, 4), db_path=setup["db_path"])
    assert result["goal_minutes"] == 60
    assert result["percent"] == 50.0


def test_weekly_goal_progress_caps_at_100_percent(setup):
    db.set_setting("weekly_goal_minutes", "10", db_path=setup["db_path"])
    log(setup, setup["sat_math"], date(2026, 10, 4), 60)

    result = stats.weekly_goal_progress(date(2026, 10, 4), db_path=setup["db_path"])
    assert result["percent"] == 100.0
