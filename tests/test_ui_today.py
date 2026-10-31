from __future__ import annotations

import os
import sys
from datetime import date

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import db
import timer


@pytest.fixture(autouse=True)
def fresh_db():
    path = os.environ["POMOLOG_DB"]
    if os.path.exists(path):
        os.remove(path)
    db.init_db()
    yield


@pytest.fixture
def static_timer(monkeypatch):
    # Fragments re-run themselves every second, so the test runner never sees them finish
    monkeypatch.setattr(st, "fragment", lambda *args, **kwargs: (lambda func: func))
    for name in ("focus",):
        sys.modules.pop(name, None)
    yield
    sys.modules.pop("focus", None)


@pytest.fixture
def subject_id():
    cat = db.create_category("School")
    return db.create_subject("SAT Math", cat)


def load_app() -> AppTest:
    return AppTest.from_file("app.py", default_timeout=15).run()


def click(at: AppTest, key: str) -> AppTest:
    at.button(key=key).click()
    return at.run()


def page_text(at: AppTest) -> str:
    parts = [m.value for m in at.markdown]
    parts += [h.proto.body for h in at.get("html")]
    return " ".join(parts)


def test_empty_state_points_to_manage():
    at = load_app()
    assert not at.exception
    assert "No subjects yet" in page_text(at)


def test_each_subject_gets_a_start_action(subject_id):
    at = load_app()
    assert not at.exception
    assert at.button(key=f"start-{subject_id}") is not None
    assert "SAT Math" in page_text(at)


def test_subject_names_are_escaped():
    cat = db.create_category("School")
    db.create_subject("<script>alert(1)</script>", cat)
    at = load_app()
    assert not at.exception
    assert "<script>" not in page_text(at)
    assert "&lt;script&gt;" in page_text(at)


def test_todays_sessions_are_listed(subject_id):
    timer.log_manual_session(subject_id, date.today(), 30)
    at = load_app()
    assert not at.exception
    assert "30m" in page_text(at)


def test_start_enters_focus_and_stop_logs(subject_id, static_timer):
    at = load_app()
    at.session_state["start-mode"] = "Free"
    at.button(key=f"start-{subject_id}").click()
    at.run()
    state = timer.get_active_timer()
    assert state is not None and state.mode == "freeform"

    at = load_app()
    assert not at.exception
    assert at.button(key="stop-timer") is not None
    assert "Return to focus" not in [b.label for b in at.button]

    at = click(at, "stop-timer")
    assert not at.exception
    assert timer.get_active_timer() is None
    assert "Timer stopped" in page_text(at) or "Logged" in page_text(at)


def test_leaving_focus_shows_today_with_a_way_back(subject_id, static_timer):
    timer.start_timer(subject_id, "freeform")
    at = load_app()
    at = click(at, "leave-focus")
    assert not at.exception
    assert any(b.label == "Return to focus" for b in at.button)
    assert not any(b.key and b.key.startswith("start-") for b in at.button)
    assert "A session is running" in page_text(at)


def test_pomodoro_start_draws_the_tide_line(subject_id, static_timer):
    at = load_app()
    at.button(key=f"start-{subject_id}").click()
    at.run()
    assert timer.get_active_timer().mode == "pomodoro"

    at = load_app()
    assert not at.exception
    assert 'class="tide"' in page_text(at)
