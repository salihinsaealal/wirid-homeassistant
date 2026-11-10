"""Parsing the Wirid stats payload (pure, no Home Assistant)."""

import pytest

from custom_components.wirid.payload import PayloadError, parse, to_dict

SAMPLE = {
    "v": 1,
    "sent": "2026-11-10T12:42:21+08:00",
    "today": {
        "total": 398, "goal": 1000, "goal_percent": 39, "tier": "emerald", "sessions": 13, "minutes": 22,
        "waktu": {"subuh": 10, "dhuha": 388},
    },
    "dhikr": {
        "subhanallah": {"name": "SubhanAllah", "today": 33, "all_time": 4000},
        "custom_random_1a2b": {"name": 'Doa "ibu" é', "today": 0, "all_time": 5, "color": "#FF8FB1", "mono": "DI"},
    },
    "week": {"total": 2000, "change": -12},
    "month": {"total": 9000, "change": None},
    "year": {"total": 40000, "change": 5},
    "streak": {"current": 1, "best": 9, "active_days": 40},
    "last_session": {"routine": "Istighfar ×100", "count": 60, "ended": "2026-11-10T12:37:18+08:00"},
}


def test_parse_v1_sample():
    s = parse(SAMPLE)
    assert (s.today_total, s.goal, s.tier, s.sessions, s.minutes) == (398, 1000, "emerald", 13, 22)
    assert s.waktu["dhuha"] == 388 and s.waktu["tahajjud"] == 0 and len(s.waktu) == 9
    assert s.app is None and s.month.change is None and s.week.change == -12
    d = {x.slug: x for x in s.dhikr}
    assert d["subhanallah"].color is None and d["custom_random_1a2b"].mono == "DI"
    assert d["custom_random_1a2b"].name == 'Doa "ibu" é'
    assert s.last_session.routine == "Istighfar ×100" and s.streak_best == 9 and s.active_days == 40


def test_parse_with_app_and_future_version():
    s = parse({**SAMPLE, "v": 7, "app": "0.4.0", "something_new": {"x": 1}})
    assert s.version == 7 and s.app == "0.4.0" and s.today_total == 398


def test_last_session_null():
    assert parse({**SAMPLE, "last_session": None}).last_session is None


def test_bad_color_dropped():
    bad = {**SAMPLE, "dhikr": {"a": {"name": "A", "today": 1, "all_time": 1, "color": "red"}}}
    assert parse(bad).dhikr[0].color is None


def test_non_numeric_becomes_zero():
    odd = {**SAMPLE, "today": {**SAMPLE["today"], "total": "lots", "minutes": None}}
    s = parse(odd)
    assert s.today_total == 0 and s.minutes == 0


@pytest.mark.parametrize("data", [None, [], "x", {}, {"v": 1}])
def test_rejects_non_snapshot(data):
    with pytest.raises(PayloadError):
        parse(data)


def test_round_trip():
    assert parse(to_dict(parse(SAMPLE))) == parse(SAMPLE)
