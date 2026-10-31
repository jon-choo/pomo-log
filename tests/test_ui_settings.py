import os

import pytest
from streamlit.testing.v1 import AppTest

import db
import stats
import timer


@pytest.fixture(autouse=True)
def fresh_db():
    path = os.environ["POMOLOG_DB"]
    if os.path.exists(path):
        os.remove(path)
    db.init_db()
    yield


def load_app() -> AppTest:
    return AppTest.from_file("views/settings.py", default_timeout=15).run()


def submit(at: AppTest, label: str) -> AppTest:
    next(b for b in at.button if b.label == label).click()
    return at.run()


def test_renders_with_defaults():
    at = load_app()
    assert not at.exception
    assert at.title[0].value == "Settings"
    assert [n.value for n in at.number_input] == [0.0, 25, 5]


def test_save_weekly_goal():
    at = load_app()
    next(n for n in at.number_input if n.label == "Hours per week").set_value(7.5)
    at = submit(at, "Save goal")
    assert not at.exception
    assert stats.weekly_goal_progress()["goal_minutes"] == 450
    assert any("Weekly goal saved" in m.value for m in at.markdown)


def test_goal_of_zero_clears_it():
    stats.set_weekly_goal(300)
    at = load_app()
    next(n for n in at.number_input if n.label == "Hours per week").set_value(0.0)
    at = submit(at, "Save goal")
    assert stats.weekly_goal_progress()["goal_minutes"] is None


def test_save_pomodoro_lengths():
    at = load_app()
    next(n for n in at.number_input if n.label == "Work minutes").set_value(50)
    next(n for n in at.number_input if n.label == "Break minutes").set_value(10)
    at = submit(at, "Save lengths")
    assert not at.exception
    assert timer.get_pomodoro_lengths() == (50, 10)
