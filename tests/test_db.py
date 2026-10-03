from datetime import timedelta

import pytest

import db
from timeutil import utc_now


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    db.init_db(path)
    return path


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

def test_create_and_list_category(db_path):
    cat_id = db.create_category("Work", db_path=db_path)
    cats = db.list_categories(db_path=db_path)
    assert len(cats) == 1
    assert cats[0]["id"] == cat_id
    assert cats[0]["name"] == "Work"
    assert cats[0]["archived"] == 0


def test_duplicate_category_name_rejected(db_path):
    db.create_category("Work", db_path=db_path)
    with pytest.raises(ValueError):
        db.create_category("Work", db_path=db_path)


def test_empty_category_name_rejected(db_path):
    with pytest.raises(ValueError):
        db.create_category("   ", db_path=db_path)


def test_rename_category(db_path):
    cat_id = db.create_category("Work", db_path=db_path)
    db.rename_category(cat_id, "School", db_path=db_path)
    assert db.get_category(cat_id, db_path=db_path)["name"] == "School"


def test_archive_category_hides_it_from_default_listing(db_path):
    cat_id = db.create_category("Work", db_path=db_path)
    db.archive_category(cat_id, db_path=db_path)
    assert db.list_categories(db_path=db_path) == []
    assert len(db.list_categories(include_archived=True, db_path=db_path)) == 1


def test_cannot_create_subject_under_archived_category(db_path):
    cat_id = db.create_category("Work", db_path=db_path)
    db.archive_category(cat_id, db_path=db_path)
    with pytest.raises(ValueError):
        db.create_subject("IT Module", cat_id, db_path=db_path)


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------

def test_create_subject(db_path):
    cat_id = db.create_category("Work", db_path=db_path)
    subj_id = db.create_subject("IT Module", cat_id, db_path=db_path)
    subjects = db.list_subjects(db_path=db_path)
    assert len(subjects) == 1
    assert subjects[0]["id"] == subj_id
    assert subjects[0]["category_id"] == cat_id


def test_create_subject_under_missing_category_rejected(db_path):
    with pytest.raises(ValueError):
        db.create_subject("IT Module", 999, db_path=db_path)


def test_duplicate_subject_within_same_category_rejected(db_path):
    cat_id = db.create_category("Work", db_path=db_path)
    db.create_subject("IT Module", cat_id, db_path=db_path)
    with pytest.raises(ValueError):
        db.create_subject("IT Module", cat_id, db_path=db_path)


def test_same_subject_name_allowed_in_different_categories(db_path):
    work = db.create_category("Work", db_path=db_path)
    school = db.create_category("School", db_path=db_path)
    db.create_subject("Reading", work, db_path=db_path)
    db.create_subject("Reading", school, db_path=db_path)  # should not raise
    assert len(db.list_subjects(db_path=db_path)) == 2


def test_recategorize_subject(db_path):
    work = db.create_category("Work", db_path=db_path)
    school = db.create_category("School", db_path=db_path)
    subj_id = db.create_subject("IT Module", work, db_path=db_path)
    db.recategorize_subject(subj_id, school, db_path=db_path)
    assert db.get_subject(subj_id, db_path=db_path)["category_id"] == school


def test_archive_subject_hides_it_from_default_listing(db_path):
    cat_id = db.create_category("Work", db_path=db_path)
    subj_id = db.create_subject("IT Module", cat_id, db_path=db_path)
    db.archive_subject(subj_id, db_path=db_path)
    assert db.list_subjects(db_path=db_path) == []
    assert len(db.list_subjects(include_archived=True, db_path=db_path)) == 1


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

def test_log_session_computes_duration_and_snapshots_category(db_path):
    cat_id = db.create_category("Work", db_path=db_path)
    subj_id = db.create_subject("IT Module", cat_id, db_path=db_path)
    start = utc_now()
    end = start + timedelta(minutes=25)
    session_id = db.log_session(subj_id, start, end, mode="pomodoro", db_path=db_path)

    session = db.get_session(session_id, db_path=db_path)
    assert session["duration_seconds"] == 25 * 60
    assert session["category_id"] == cat_id
    assert session["mode"] == "pomodoro"


def test_log_session_survives_subject_recategorization(db_path):
    work = db.create_category("Work", db_path=db_path)
    school = db.create_category("School", db_path=db_path)
    subj_id = db.create_subject("IT Module", work, db_path=db_path)
    start = utc_now()
    session_id = db.log_session(subj_id, start, start + timedelta(minutes=10), mode="manual", db_path=db_path)

    db.recategorize_subject(subj_id, school, db_path=db_path)

    # historical session still points at the category it was logged under
    assert db.get_session(session_id, db_path=db_path)["category_id"] == work


def test_log_session_rejects_end_before_start(db_path):
    cat_id = db.create_category("Work", db_path=db_path)
    subj_id = db.create_subject("IT Module", cat_id, db_path=db_path)
    start = utc_now()
    with pytest.raises(ValueError):
        db.log_session(subj_id, start, start - timedelta(minutes=5), mode="freeform", db_path=db_path)


def test_log_session_rejects_invalid_mode(db_path):
    cat_id = db.create_category("Work", db_path=db_path)
    subj_id = db.create_subject("IT Module", cat_id, db_path=db_path)
    start = utc_now()
    with pytest.raises(ValueError):
        db.log_session(subj_id, start, start + timedelta(minutes=5), mode="nonsense", db_path=db_path)


def test_update_session_recomputes_duration(db_path):
    cat_id = db.create_category("Work", db_path=db_path)
    subj_id = db.create_subject("IT Module", cat_id, db_path=db_path)
    start = utc_now()
    session_id = db.log_session(subj_id, start, start + timedelta(minutes=25), mode="pomodoro", db_path=db_path)

    db.update_session(session_id, end_time=start + timedelta(minutes=40), db_path=db_path)
    assert db.get_session(session_id, db_path=db_path)["duration_seconds"] == 40 * 60


def test_delete_session(db_path):
    cat_id = db.create_category("Work", db_path=db_path)
    subj_id = db.create_subject("IT Module", cat_id, db_path=db_path)
    start = utc_now()
    session_id = db.log_session(subj_id, start, start + timedelta(minutes=5), mode="manual", db_path=db_path)

    db.delete_session(session_id, db_path=db_path)
    assert db.get_session(session_id, db_path=db_path) is None


def test_list_sessions_filters_by_time_range(db_path):
    cat_id = db.create_category("Work", db_path=db_path)
    subj_id = db.create_subject("IT Module", cat_id, db_path=db_path)
    now = utc_now()
    old_session = db.log_session(
        subj_id, now - timedelta(days=10), now - timedelta(days=10) + timedelta(minutes=5),
        mode="manual", db_path=db_path,
    )
    recent_session = db.log_session(
        subj_id, now, now + timedelta(minutes=5), mode="manual", db_path=db_path,
    )

    results = db.list_sessions(start=now - timedelta(days=1), db_path=db_path)
    ids = [s["id"] for s in results]
    assert ids == [recent_session]
    assert old_session not in ids


def test_list_sessions_newest_first_by_default(db_path):
    cat_id = db.create_category("Work", db_path=db_path)
    subj_id = db.create_subject("IT Module", cat_id, db_path=db_path)
    now = utc_now()
    first = db.log_session(subj_id, now, now + timedelta(minutes=5), mode="manual", db_path=db_path)
    second = db.log_session(
        subj_id, now + timedelta(hours=1), now + timedelta(hours=1, minutes=5), mode="manual", db_path=db_path
    )

    results = db.list_sessions(db_path=db_path)
    assert [s["id"] for s in results] == [second, first]


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def test_setting_roundtrip_and_default(db_path):
    assert db.get_setting("pomodoro_work_minutes", default="25", db_path=db_path) == "25"
    db.set_setting("pomodoro_work_minutes", "30", db_path=db_path)
    assert db.get_setting("pomodoro_work_minutes", db_path=db_path) == "30"


def test_set_setting_overwrites_existing_value(db_path):
    db.set_setting("weekly_goal_minutes", "600", db_path=db_path)
    db.set_setting("weekly_goal_minutes", "900", db_path=db_path)
    assert db.get_setting("weekly_goal_minutes", db_path=db_path) == "900"
