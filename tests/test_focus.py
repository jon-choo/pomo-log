from datetime import datetime, timezone

import pytest

import focus
import timer

T0 = datetime(2026, 10, 4, 1, 0, 0, tzinfo=timezone.utc)


def pomodoro_state(work=25 * 60, rest=5 * 60):
    return timer.TimerState(
        subject_id=1, mode="pomodoro", started_at=T0, work_seconds=work, break_seconds=rest
    )


def test_numeral_uses_fixed_cells_for_digits_and_colon():
    out = focus.numeral_html(24 * 60 + 57)
    assert out.count('class="d"') == 4
    assert out.count('class="c"') == 1


def test_tide_level_rises_through_work_and_falls_through_break():
    work, rest = 1500, 300
    assert focus.tide_level(0, work, rest) == pytest.approx(0)
    assert focus.tide_level(work, work, rest) == pytest.approx(1)
    assert focus.tide_level(work + rest, work, rest) == pytest.approx(0)
    assert focus.tide_level(300, work, rest) < focus.tide_level(900, work, rest)
    assert focus.tide_level(work + 60, work, rest) > focus.tide_level(work + 240, work, rest)


def test_tide_svg_marks_the_current_position():
    state = pomodoro_state()
    svg = focus.tide_svg(state, elapsed=600)
    assert 'class="elapsed"' in svg and 'class="remaining"' in svg
    html = focus.tide_html(state, elapsed=600)
    assert "Work 25:00" in html and "Break 05:00" in html and "data:image/svg+xml" in html


def test_tide_svg_wraps_to_the_next_cycle():
    state = pomodoro_state()
    first = focus.tide_svg(state, elapsed=600)
    next_cycle = focus.tide_svg(state, elapsed=600 + 30 * 60)
    assert first == next_cycle


def test_tide_svg_at_the_very_start_has_no_elapsed_stroke_length():
    svg = focus.tide_svg(pomodoro_state(), elapsed=0)
    assert 'class="elapsed" d="M' in svg


def test_phase_caption():
    state = pomodoro_state()
    assert focus.phase_caption(state, timer.phase_info(state, T0)) == "Work, interval 1"
    after = T0.replace(hour=1, minute=26)
    assert focus.phase_caption(state, timer.phase_info(state, after)) == "Break, after interval 1"
    free = timer.TimerState(subject_id=1, mode="freeform", started_at=T0)
    assert focus.phase_caption(free, timer.phase_info(free, T0)) == "Free, counting up"
