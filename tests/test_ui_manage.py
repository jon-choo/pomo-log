import os

import pytest
from streamlit.testing.v1 import AppTest

import db


@pytest.fixture(autouse=True)
def fresh_db():
    path = os.environ["POMOLOG_DB"]
    if os.path.exists(path):
        os.remove(path)
    db.init_db()
    yield


def load_app() -> AppTest:
    return AppTest.from_file("views/manage.py", default_timeout=15).run()


def submit(at: AppTest, label: str) -> AppTest:
    next(b for b in at.button if b.label == label).click()
    return at.run()


def test_empty_state_renders_without_errors():
    at = load_app()
    assert not at.exception
    assert at.title[0].value == "Manage"
    assert any("No categories yet" in m.value for m in at.markdown)


def test_add_category_then_subject():
    at = load_app()
    at.text_input[0].set_value("School")
    at = submit(at, "Add category")
    assert not at.exception
    assert [c["name"] for c in db.list_categories()] == ["School"]
    assert any("Added category 'School'" in s.value for s in at.success)

    next(t for t in at.text_input if t.label == "New subject").set_value("SAT Math")
    at = submit(at, "Add subject")
    assert not at.exception
    assert [s["name"] for s in db.list_subjects()] == ["SAT Math"]


def test_duplicate_category_shows_an_error_instead_of_crashing():
    db.create_category("School")
    at = load_app()
    at.text_input[0].set_value("School")
    at = submit(at, "Add category")
    assert not at.exception
    assert any("already exists" in e.value for e in at.error)


def test_archive_is_disabled_while_category_has_subjects():
    cat = db.create_category("School")
    db.create_subject("SAT Math", cat)
    at = load_app()
    archive_buttons = [b for b in at.button if b.label == "Archive"]
    assert archive_buttons[0].disabled  # the category row
