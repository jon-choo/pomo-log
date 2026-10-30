"""Display formatting for durations."""


def format_duration(seconds: int) -> str:
    if 0 < seconds < 60:
        return f"{int(seconds)}s"
    hours, minutes = divmod(int(seconds) // 60, 60)
    if hours:
        return f"{hours}h" if minutes == 0 else f"{hours}h {minutes:02d}m"
    return f"{minutes}m"


def format_clock(seconds: int) -> str:
    hours, remainder = divmod(max(0, int(seconds)), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
