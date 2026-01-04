"""Date calculator utilities and small CLI.

Features:
- parse/format ISO dates
- add/subtract days
- add business days
- add months (calendar-aware)
- difference in days/weeks/months
- weekday name

Usage:
    python date_calculator.py add-days 2026-01-03 10
    python date_calculator.py diff 2026-01-03 2025-12-25
    python date_calculator.py business-add 2026-01-01 10
    python date_calculator.py weekday 2026-01-03

"""
from __future__ import annotations
import sys
from datetime import datetime, date, timedelta
import calendar
from typing import Tuple

ISO = "%Y-%m-%d"


def parse_date(s: str) -> date:
    s = s.strip()
    # try several common formats
    for fmt in (ISO, "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    # try ISO parse fallback
    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        raise ValueError(f"Unrecognized date format: {s}")


def format_date(d: date) -> str:
    return d.strftime(ISO)


def add_days(d: date, days: int) -> date:
    return d + timedelta(days=days)


def diff_days(a: date, b: date) -> int:
    """Return a - b in days (signed)."""
    return (a - b).days


def weekday_name(d: date) -> str:
    return calendar.day_name[d.weekday()]


def add_business_days(d: date, n: int) -> date:
    sign = 1 if n >= 0 else -1
    remaining = abs(n)
    cur = d
    while remaining > 0:
        cur = cur + timedelta(days=sign)
        if cur.weekday() < 5:  # Mon-Fri
            remaining -= 1
    return cur


def add_months(d: date, months: int) -> date:
    # Advance by months preserving day where possible
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    day = min(d.day, calendar.monthrange(y, m)[1])
    return date(y, m, day)


def diff_years_months_days(a: date, b: date) -> Tuple[int,int,int]:
    # compute a - b in years, months, days (approx exact calendar difference)
    if a < b:
        sign = -1
        a, b = b, a
    else:
        sign = 1
    y = a.year - b.year
    m = a.month - b.month
    d = a.day - b.day
    if d < 0:
        m -= 1
        prev_month = (a.month - 1) or 12
        prev_year = a.year if a.month != 1 else a.year - 1
        d += calendar.monthrange(prev_year, prev_month)[1]
    if m < 0:
        y -= 1
        m += 12
    return (sign*y, m, d)


def cli(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(__doc__)
        return 0
    cmd = argv[0]
    try:
        if cmd == 'add-days' and len(argv) == 3:
            d = parse_date(argv[1])
            n = int(argv[2])
            print(format_date(add_days(d, n)))
        elif cmd == 'diff' and len(argv) == 3:
            a = parse_date(argv[1])
            b = parse_date(argv[2])
            print(diff_days(a, b))
        elif cmd == 'business-add' and len(argv) == 3:
            d = parse_date(argv[1])
            n = int(argv[2])
            print(format_date(add_business_days(d, n)))
        elif cmd == 'weekday' and len(argv) == 2:
            d = parse_date(argv[1])
            print(weekday_name(d))
        elif cmd == 'add-months' and len(argv) == 3:
            d = parse_date(argv[1])
            n = int(argv[2])
            print(format_date(add_months(d, n)))
        elif cmd == 'diff-ymd' and len(argv) == 3:
            a = parse_date(argv[1])
            b = parse_date(argv[2])
            y, m, day = diff_years_months_days(a, b)
            print(f"{y} years, {m} months, {day} days")
        else:
            print('Unknown command or wrong args. See usage:')
            print(__doc__)
            return 2
    except Exception as e:
        print('Error:', e)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(cli())
