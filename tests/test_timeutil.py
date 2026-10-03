from datetime import date, datetime, timedelta, timezone

import pytest

from timeutil import SGT, day_bounds_utc, sgt_date, to_sgt, week_bounds_utc, week_start_date


def test_to_sgt_rejects_naive_datetime():
    with pytest.raises(ValueError):
        to_sgt(datetime(2026, 1, 1))


def test_sgt_date_at_midnight_boundary():
    # SGT = UTC+8, so SGT midnight on Jan 2 is 16:00 UTC on Jan 1.
    just_before = datetime(2026, 1, 1, 15, 59, 59, tzinfo=timezone.utc)
    just_after = datetime(2026, 1, 1, 16, 0, 0, tzinfo=timezone.utc)
    assert sgt_date(just_before) == date(2026, 1, 1)
    assert sgt_date(just_after) == date(2026, 1, 2)


@pytest.mark.parametrize(
    "day, expected_sunday",
    [
        (date(2026, 9, 27), date(2026, 9, 27)),  # a Sunday maps to itself
        (date(2026, 9, 28), date(2026, 9, 27)),  # Monday -> previous Sunday
        (date(2026, 10, 3), date(2026, 9, 27)),  # Saturday -> start of its week
    ],
)
def test_week_start_date(day, expected_sunday):
    assert week_start_date(day) == expected_sunday


def test_day_bounds_utc_spans_exactly_24_hours_in_sgt():
    start, end = day_bounds_utc(date(2026, 9, 28))
    assert end - start == timedelta(days=1)
    assert to_sgt(start) == datetime(2026, 9, 28, 0, 0, tzinfo=SGT)
    assert to_sgt(end) == datetime(2026, 9, 29, 0, 0, tzinfo=SGT)


def test_week_bounds_utc_spans_exactly_7_days_and_starts_on_sunday():
    start, end = week_bounds_utc(date(2026, 10, 3))  # a Saturday
    assert end - start == timedelta(days=7)
    assert to_sgt(start) == datetime(2026, 9, 27, 0, 0, tzinfo=SGT)  # the Sunday before
    assert to_sgt(end) == datetime(2026, 10, 4, 0, 0, tzinfo=SGT)


def test_week_bounds_utc_agrees_with_day_bounds_utc_on_the_sunday():
    sunday = week_start_date(date(2026, 10, 3))
    week_start, _ = week_bounds_utc(sunday)
    day_start, _ = day_bounds_utc(sunday)
    assert week_start == day_start
