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
    # The live panel re-runs itself every second, so the test runner never sees it finish
    monkeypatch.setattr(st, "fragment", lambda *args, **kwargs: (lambda func: func))
    sys.modules.pop("timer_ui", None)
    yield
    sys.modules.pop("timer_ui", None)


@pytest.fixture
def subject_id():
    cat = db.create_category("School")
    return db.create_subject("SAT Math", cat)


def load_app(subject: int | None = None) -> AppTest:
    at = AppTest.from_file("app.py", default_timeout=15)
    if subject is not None:
        at.query_params["subject"] = str(subject)
    return at.run()


def click(at: AppTest, label: str) -> AppTest:
    next(b for b in at.button if b.label == label).click()
    return at.run()


def page_html(at: AppTest) -> str:
    return " ".join(m.value for m in at.markdown)


def test_empty_state_points_to_manage():
    at = load_app()
    assert not at.exception
    assert "No subjects yet" in page_html(at)


def test_grid_shows_a_card_with_the_subject_color(subject_id):
    at = load_app()
    assert not at.exception
    color = db.get_subject(subject_id)["color"]
    assert "SAT Math" in page_html(at)
    assert color in page_html(at)
    assert any(b.label == "Open SAT Math" for b in at.button)


def test_subject_names_are_escaped_in_html():
    cat = db.create_category("School")
    db.create_subject("<script>alert(1)</script>", cat)
    at = load_app()
    assert not at.exception
    assert "<script>" not in page_html(at)
    assert "&lt;script&gt;" in page_html(at)


def test_clicking_a_card_opens_the_subject_page(subject_id):
    at = click(load_app(), "Open SAT Math")
    assert not at.exception
    assert at.query_params["subject"] == [str(subject_id)]
    assert any(b.label == "Start" for b in at.button)
    assert any(b.label == "All subjects" for b in at.button)


def test_back_button_returns_to_the_grid(subject_id):
    at = click(load_app(subject_id), "All subjects")
    assert not at.exception
    assert any(b.label == "Open SAT Math" for b in at.button)


def test_archived_subject_link_falls_back_to_the_grid(subject_id):
    db.archive_subject(subject_id)
    at = load_app(subject_id)
    assert not at.exception
    assert "No subjects yet" in page_html(at)


def test_start_then_stop_a_free_timer_logs_a_session(subject_id, static_timer):
    at = load_app(subject_id)
    next(r for r in at.radio if r.label == "Mode").set_value("Free")
    at = click(at, "Start")
    assert not at.exception
    state = timer.get_active_timer()
    assert state is not None and state.mode == "freeform"
    assert any(b.label == "Stop" for b in at.button)

    at = click(at, "Stop")
    assert not at.exception
    assert timer.get_active_timer() is None


def test_recent_sessions_listed_on_the_subject_page(subject_id):
    timer.log_manual_session(subject_id, date.today(), 30)
    at = load_app(subject_id)
    assert not at.exception
    assert "30m" in page_html(at)
