from datetime import date, datetime, timedelta, timezone

import pytest

import db
import timer
from timeutil import day_bounds_utc

T0 = datetime(2026, 10, 4, 1, 0, 0, tzinfo=timezone.utc)


def minutes(n):
    return timedelta(minutes=n)


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    db.init_db(path)
    return path


@pytest.fixture
def subject_id(db_path):
    cat = db.create_category("School", db_path=db_path)
    return db.create_subject("SAT Math", cat, db_path=db_path)


# Pomodoro length settings

def test_pomodoro_lengths_default_to_25_and_5(db_path):
    assert timer.get_pomodoro_lengths(db_path) == (25, 5)


def test_set_pomodoro_lengths_roundtrip(db_path):
    timer.set_pomodoro_lengths(50, 10, db_path)
    assert timer.get_pomodoro_lengths(db_path) == (50, 10)


def test_set_pomodoro_lengths_rejects_non_positive(db_path):
    with pytest.raises(ValueError):
        timer.set_pomodoro_lengths(0, 5, db_path)
    with pytest.raises(ValueError):
        timer.set_pomodoro_lengths(25, 0, db_path)


# Starting

def test_start_timer_persists_state(db_path, subject_id):
    timer.start_timer(subject_id, "freeform", now=T0, db_path=db_path)
    state = timer.get_active_timer(db_path)
    assert state.subject_id == subject_id
    assert state.mode == "freeform"
    assert state.started_at == T0


def test_no_active_timer_by_default(db_path):
    assert timer.get_active_timer(db_path) is None


def test_cannot_start_second_timer(db_path, subject_id):
    timer.start_timer(subject_id, "freeform", now=T0, db_path=db_path)
    with pytest.raises(ValueError):
        timer.start_timer(subject_id, "pomodoro", now=T0, db_path=db_path)


def test_start_rejects_missing_archived_subject_and_bad_mode(db_path, subject_id):
    with pytest.raises(ValueError):
        timer.start_timer(999, "freeform", now=T0, db_path=db_path)
    with pytest.raises(ValueError):
        timer.start_timer(subject_id, "nonsense", now=T0, db_path=db_path)
    db.archive_subject(subject_id, db_path=db_path)
    with pytest.raises(ValueError):
        timer.start_timer(subject_id, "freeform", now=T0, db_path=db_path)


def test_pomodoro_lengths_are_snapshotted_at_start(db_path, subject_id):
    timer.set_pomodoro_lengths(30, 10, db_path)
    timer.start_timer(subject_id, "pomodoro", now=T0, db_path=db_path)
    timer.set_pomodoro_lengths(50, 15, db_path)  # changed mid-run

    state = timer.get_active_timer(db_path)
    assert (state.work_seconds, state.break_seconds) == (30 * 60, 10 * 60)


# Phases

def test_phase_info_freeform(db_path, subject_id):
    state = timer.start_timer(subject_id, "freeform", now=T0, db_path=db_path)
    info = timer.phase_info(state, T0 + minutes(12))
    assert info["phase"] == "free"
    assert info["elapsed_seconds"] == 12 * 60
    assert info["phase_remaining_seconds"] is None


def test_phase_info_walks_work_break_work_break(db_path, subject_id):
    state = timer.start_timer(subject_id, "pomodoro", now=T0, db_path=db_path)  # 25/5

    work1 = timer.phase_info(state, T0 + minutes(10))
    assert work1["phase"] == "work"
    assert work1["phase_remaining_seconds"] == 15 * 60
    assert work1["completed_work_intervals"] == 0

    break1 = timer.phase_info(state, T0 + minutes(26))
    assert break1["phase"] == "break"
    assert break1["phase_elapsed_seconds"] == 60
    assert break1["phase_remaining_seconds"] == 4 * 60
    assert break1["completed_work_intervals"] == 1

    work2 = timer.phase_info(state, T0 + minutes(31))
    assert work2["phase"] == "work"
    assert work2["completed_work_intervals"] == 1

    break2 = timer.phase_info(state, T0 + minutes(56))
    assert break2["phase"] == "break"
    assert break2["completed_work_intervals"] == 2


def test_phase_info_clamps_clock_skew_to_zero_elapsed(db_path, subject_id):
    state = timer.start_timer(subject_id, "pomodoro", now=T0, db_path=db_path)
    info = timer.phase_info(state, T0 - minutes(5))
    assert info["elapsed_seconds"] == 0
    assert info["phase"] == "work"


# Tick

def test_tick_does_nothing_without_a_timer(db_path):
    assert timer.tick(now=T0, db_path=db_path) == []


def test_tick_logs_nothing_before_first_interval_finishes(db_path, subject_id):
    timer.start_timer(subject_id, "pomodoro", now=T0, db_path=db_path)
    assert timer.tick(now=T0 + minutes(24), db_path=db_path) == []
    assert db.list_sessions(db_path=db_path) == []


def test_tick_logs_finished_work_interval_once(db_path, subject_id):
    timer.start_timer(subject_id, "pomodoro", now=T0, db_path=db_path)

    first = timer.tick(now=T0 + minutes(26), db_path=db_path)
    again = timer.tick(now=T0 + minutes(27), db_path=db_path)

    assert len(first) == 1
    assert again == []
    session = db.get_session(first[0], db_path=db_path)
    assert session["mode"] == "pomodoro"
    assert session["duration_seconds"] == 25 * 60
    assert datetime.fromisoformat(session["start_time"]) == T0
    assert datetime.fromisoformat(session["end_time"]) == T0 + minutes(25)


def test_tick_catches_up_on_multiple_intervals_after_a_long_gap(db_path, subject_id):
    timer.start_timer(subject_id, "pomodoro", now=T0, db_path=db_path)

    ids = timer.tick(now=T0 + minutes(56), db_path=db_path)  # UI wasn't open for a while

    assert len(ids) == 2
    starts = sorted(datetime.fromisoformat(db.get_session(i, db_path=db_path)["start_time"]) for i in ids)
    assert starts == [T0, T0 + minutes(30)]


def test_tick_never_logs_freeform(db_path, subject_id):
    timer.start_timer(subject_id, "freeform", now=T0, db_path=db_path)
    assert timer.tick(now=T0 + minutes(120), db_path=db_path) == []


# Stop

def test_stop_without_timer_raises(db_path):
    with pytest.raises(ValueError):
        timer.stop_timer(now=T0, db_path=db_path)


def test_stop_freeform_logs_one_session_and_clears_timer(db_path, subject_id):
    timer.start_timer(subject_id, "freeform", now=T0, db_path=db_path)
    ids = timer.stop_timer(now=T0 + minutes(42), db_path=db_path)

    assert len(ids) == 1
    session = db.get_session(ids[0], db_path=db_path)
    assert session["mode"] == "freeform"
    assert session["duration_seconds"] == 42 * 60
    assert timer.get_active_timer(db_path) is None


def test_stop_immediately_logs_nothing_and_does_not_error(db_path, subject_id):
    timer.start_timer(subject_id, "freeform", now=T0, db_path=db_path)
    assert timer.stop_timer(now=T0, db_path=db_path) == []
    assert timer.get_active_timer(db_path) is None


def test_stop_pomodoro_mid_work_logs_partial_interval(db_path, subject_id):
    timer.start_timer(subject_id, "pomodoro", now=T0, db_path=db_path)
    ids = timer.stop_timer(now=T0 + minutes(10), db_path=db_path)

    assert len(ids) == 1
    assert db.get_session(ids[0], db_path=db_path)["duration_seconds"] == 10 * 60


def test_stop_pomodoro_during_break_logs_only_completed_work(db_path, subject_id):
    timer.start_timer(subject_id, "pomodoro", now=T0, db_path=db_path)
    ids = timer.stop_timer(now=T0 + minutes(27), db_path=db_path)

    assert len(ids) == 1
    assert db.get_session(ids[0], db_path=db_path)["duration_seconds"] == 25 * 60


def test_stop_pomodoro_mid_second_interval_logs_full_plus_partial(db_path, subject_id):
    timer.start_timer(subject_id, "pomodoro", now=T0, db_path=db_path)
    ids = timer.stop_timer(now=T0 + minutes(40), db_path=db_path)  # 25 work, 5 break, 10 work

    durations = sorted(db.get_session(i, db_path=db_path)["duration_seconds"] for i in ids)
    assert durations == [10 * 60, 25 * 60]


def test_stop_does_not_double_log_intervals_already_ticked(db_path, subject_id):
    timer.start_timer(subject_id, "pomodoro", now=T0, db_path=db_path)
    timer.tick(now=T0 + minutes(26), db_path=db_path)
    timer.stop_timer(now=T0 + minutes(28), db_path=db_path)

    assert len(db.list_sessions(db_path=db_path)) == 1


def test_can_start_a_new_timer_after_stopping(db_path, subject_id):
    timer.start_timer(subject_id, "freeform", now=T0, db_path=db_path)
    timer.stop_timer(now=T0 + minutes(5), db_path=db_path)
    timer.start_timer(subject_id, "pomodoro", now=T0 + minutes(10), db_path=db_path)  # no error
    assert timer.get_active_timer(db_path) is not None


# Manual entry

def test_manual_session_lands_on_the_right_sgt_day(db_path, subject_id):
    day = date(2026, 10, 1)
    session_id = timer.log_manual_session(subject_id, day, 45, today=date(2026, 10, 4), db_path=db_path)

    session = db.get_session(session_id, db_path=db_path)
    assert session["mode"] == "manual"
    assert session["duration_seconds"] == 45 * 60

    start, end = day_bounds_utc(day)
    in_day = db.list_sessions(start=start, end=end, db_path=db_path)
    assert [s["id"] for s in in_day] == [session_id]


def test_manual_session_allows_today(db_path, subject_id):
    today = date(2026, 10, 4)
    timer.log_manual_session(subject_id, today, 10, today=today, db_path=db_path)  # no error


def test_manual_session_rejects_future_date(db_path, subject_id):
    with pytest.raises(ValueError):
        timer.log_manual_session(subject_id, date(2026, 10, 5), 10, today=date(2026, 10, 4), db_path=db_path)


def test_manual_session_rejects_bad_durations(db_path, subject_id):
    today = date(2026, 10, 4)
    with pytest.raises(ValueError):
        timer.log_manual_session(subject_id, today, 0, today=today, db_path=db_path)
    with pytest.raises(ValueError):
        timer.log_manual_session(subject_id, today, 24 * 60 + 1, today=today, db_path=db_path)


def test_manual_session_rejects_unknown_subject(db_path):
    today = date(2026, 10, 4)
    with pytest.raises(ValueError):
        timer.log_manual_session(999, today, 10, today=today, db_path=db_path)
