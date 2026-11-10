"""The Wirid stats payload: parsing and serialising. Pure Python, no Home Assistant imports.

The app sends one JSON snapshot (`v: 1`). Later app versions add optional fields (`app`, and per
dhikr `color`, `mono`); unknown fields and higher versions are tolerated, so a newer app never
breaks an older integration. Numbers that aren't numbers become 0 rather than failing the post.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from .const import WAKTU

_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


class PayloadError(ValueError):
    """The posted data is not a Wirid snapshot."""


@dataclass(frozen=True)
class Dhikr:
    slug: str
    name: str
    today: int
    all_time: int
    color: str | None
    mono: str | None
    days: tuple[int, ...] | None = None


@dataclass(frozen=True)
class Period:
    total: int
    change: int | None


@dataclass(frozen=True)
class LastSession:
    routine: str
    count: int
    ended: str


@dataclass(frozen=True)
class Snapshot:
    version: int
    sent: str
    app: str | None
    today_total: int
    goal: int
    goal_percent: int
    tier: str
    sessions: int
    minutes: int
    waktu: dict[str, int]
    dhikr: tuple[Dhikr, ...]
    week: Period
    month: Period
    year: Period
    streak_current: int
    streak_best: int
    active_days: int
    last_session: LastSession | None
    days: tuple[str, ...] | None = None


_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MAX_DAYS = 31


def _days_counts(value: Any) -> tuple[int, ...] | None:
    """Per-day counts (oldest first); None when absent or not a list."""
    return tuple(_int(v) for v in value[:_MAX_DAYS]) if isinstance(value, list) else None


def _days_dates(value: Any) -> tuple[str, ...] | None:
    """The dates of the per-day counts (ISO, oldest first); entries that aren't dates are skipped."""
    if not isinstance(value, list):
        return None
    return tuple(v for v in value if isinstance(v, str) and _DATE.match(v))[:_MAX_DAYS]


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return 0
    return 0


def _opt_int(value: Any) -> int | None:
    return None if value is None else _int(value)


def _str(value: Any, default: str = "") -> str:
    return value if isinstance(value, str) else default


def _obj(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _period(value: Any) -> Period:
    p = _obj(value)
    return Period(_int(p.get("total")), _opt_int(p.get("change")))


def parse(data: object) -> Snapshot:
    """Parse a posted snapshot; raises PayloadError when it isn't one."""
    if not isinstance(data, dict) or not isinstance(data.get("today"), dict):
        raise PayloadError("not a Wirid snapshot")
    today = data["today"]
    waktu_in = _obj(today.get("waktu"))
    dhikr = []
    for slug, raw in _obj(data.get("dhikr")).items():
        d = _obj(raw)
        color = d.get("color")
        mono = d.get("mono")
        dhikr.append(
            Dhikr(
                slug=str(slug),
                name=_str(d.get("name"), str(slug)),
                today=_int(d.get("today")),
                all_time=_int(d.get("all_time")),
                color=color if isinstance(color, str) and _COLOR.match(color) else None,
                mono=mono if isinstance(mono, str) and mono else None,
                days=_days_counts(d.get("days")),
            )
        )
    streak = _obj(data.get("streak"))
    last = data.get("last_session")
    last_session = None
    if isinstance(last, dict):
        last_session = LastSession(_str(last.get("routine")), _int(last.get("count")), _str(last.get("ended")))
    app = data.get("app")
    return Snapshot(
        version=_int(data.get("v")) or 1,
        sent=_str(data.get("sent")),
        app=app if isinstance(app, str) and app else None,
        today_total=_int(today.get("total")),
        goal=_int(today.get("goal")),
        goal_percent=_int(today.get("goal_percent")),
        tier=_str(today.get("tier"), "emerald"),
        sessions=_int(today.get("sessions")),
        minutes=_int(today.get("minutes")),
        waktu={w: _int(waktu_in.get(w)) for w in WAKTU},
        dhikr=tuple(dhikr),
        week=_period(data.get("week")),
        month=_period(data.get("month")),
        year=_period(data.get("year")),
        streak_current=_int(streak.get("current")),
        streak_best=_int(streak.get("best")),
        active_days=_int(streak.get("active_days")),
        last_session=last_session,
        days=_days_dates(data.get("days")),
    )


def to_dict(s: Snapshot) -> dict:
    """The snapshot back in payload form (for storage); parse(to_dict(s)) == s."""
    dhikr: dict[str, dict] = {}
    for d in s.dhikr:
        item: dict[str, Any] = {"name": d.name, "today": d.today, "all_time": d.all_time}
        if d.color is not None:
            item["color"] = d.color
        if d.mono is not None:
            item["mono"] = d.mono
        if d.days is not None:
            item["days"] = list(d.days)
        dhikr[d.slug] = item
    out: dict[str, Any] = {
        "v": s.version,
        "sent": s.sent,
        "today": {
            "total": s.today_total, "goal": s.goal, "goal_percent": s.goal_percent, "tier": s.tier,
            "sessions": s.sessions, "minutes": s.minutes, "waktu": dict(s.waktu),
        },
        "dhikr": dhikr,
        "week": {"total": s.week.total, "change": s.week.change},
        "month": {"total": s.month.total, "change": s.month.change},
        "year": {"total": s.year.total, "change": s.year.change},
        "streak": {"current": s.streak_current, "best": s.streak_best, "active_days": s.active_days},
        "last_session": None if s.last_session is None else {
            "routine": s.last_session.routine, "count": s.last_session.count, "ended": s.last_session.ended,
        },
    }
    if s.app is not None:
        out["app"] = s.app
    if s.days is not None:
        out["days"] = list(s.days)
    return out
