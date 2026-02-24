"""Evaluate 5-field cron expressions against a datetime.

Supports: *, comma lists, ranges (1-5), steps (*/10, 1-5/2).
DOW: 0 and 7 both mean Sunday (cron convention).
"""

from datetime import datetime


def _parse_field(field: str, min_val: int, max_val: int) -> set[int]:
    """Parse a single cron field into a set of matching integers."""
    result = set()
    for part in field.split(","):
        if "/" in part:
            base, step = part.split("/", 1)
            step = int(step)
        else:
            base = part
            step = None

        if base == "*":
            start, end = min_val, max_val
        elif "-" in base:
            start, end = (int(x) for x in base.split("-", 1))
        else:
            start = end = int(base)

        if step:
            result.update(range(start, end + 1, step))
        else:
            result.update(range(start, end + 1))

    return result


def matches_now(expr: str, now: datetime | None = None) -> bool:
    """Return True if `expr` matches the given (or current) minute.

    expr: "minute hour dom month dow" — standard 5-field cron.
    """
    if now is None:
        now = datetime.now()

    fields = expr.strip().split()
    if len(fields) != 5:
        raise ValueError(f"Expected 5 cron fields, got {len(fields)}: {expr!r}")

    minute, hour, dom, month, dow = fields

    minutes = _parse_field(minute, 0, 59)
    hours = _parse_field(hour, 0, 23)
    doms = _parse_field(dom, 1, 31)
    months = _parse_field(month, 1, 12)
    dows = _parse_field(dow, 0, 7)
    # Normalize: cron uses 0=Sun and 7=Sun; Python weekday() uses 0=Mon..6=Sun
    py_dow = now.weekday()  # 0=Mon..6=Sun
    cron_dow = (py_dow + 1) % 7  # 0=Sun..6=Sat

    return (
        now.minute in minutes
        and now.hour in hours
        and now.day in doms
        and now.month in months
        and cron_dow in dows
    )
