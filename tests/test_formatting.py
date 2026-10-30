from formatting import format_clock, format_duration


def test_format_duration():
    assert format_duration(0) == "0m"
    assert format_duration(14) == "14s"
    assert format_duration(60) == "1m"
    assert format_duration(45 * 60) == "45m"
    assert format_duration(3600) == "1h"
    assert format_duration(3 * 3600 + 5 * 60) == "3h 05m"


def test_format_clock():
    assert format_clock(0) == "00:00"
    assert format_clock(24 * 60 + 47) == "24:47"
    assert format_clock(3600 + 65) == "1:01:05"
    assert format_clock(-5) == "00:00"
