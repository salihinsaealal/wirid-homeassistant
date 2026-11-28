"""The today-total sensor's `color`: the tier colour for today's lap, as the cards and the watch face show it."""

import copy
import json
import re
from pathlib import Path

import pytest

from custom_components.wirid.const import TIER_COLORS, TIER_KEYS
from custom_components.wirid.sensor import tier_color
from tests.test_payload import SAMPLE
from tests.test_sensor import _post, _setup

CORE_JS = Path(__file__).resolve().parent.parent / "custom_components/wirid/frontend/wirid-core.js"
HEX = re.compile(r"^#[0-9A-F]{6}$")


def test_colours_match_the_cards():
    found = re.search(r"export const TIERS = (\[[^\]]*\]);", CORE_JS.read_text(encoding="utf-8"))
    assert found, "TIERS not found in wirid-core.js"
    assert list(TIER_COLORS) == json.loads(found.group(1))


def test_five_tiers_all_rrggbb():
    assert TIER_KEYS == ("emerald", "gold", "blue", "pink", "silver")
    assert len(TIER_COLORS) == 5 and all(HEX.match(c) for c in TIER_COLORS)


@pytest.mark.parametrize(("key", "colour"), [
    ("emerald", "#34E3A0"), ("gold", "#FFD84D"), ("blue", "#3FA9FF"), ("pink", "#FF9ECF"), ("silver", "#E4ECF7"),
])
def test_colour_from_tier_key(key, colour):
    # The key wins over the totals (here they'd say lap 1).
    assert tier_color(key, 0, 1000) == colour


@pytest.mark.parametrize(("total", "goal", "colour"), [
    (500, 0, "#34E3A0"),       # no goal: lap 1
    (999, 1000, "#34E3A0"),    # under the goal
    (1000, 1000, "#FFD84D"),   # exactly 1×: reaching the goal opens lap 2
    (2000, 1000, "#3FA9FF"),   # 2×: lap 3
    (6000, 1000, "#E4ECF7"),   # 6×: lap 7, capped at silver
])
def test_unknown_key_falls_back_to_lap(total, goal, colour):
    assert tier_color("purple?", total, goal) == colour
    assert tier_color("", total, goal) == colour


async def test_today_total_has_color(hass, hass_client_no_auth):
    await _setup(hass)
    s = hass.states.get("sensor.wirid_today_total")
    assert s.attributes["color"] == "#34E3A0"  # no data yet: emerald, never empty
    client = await hass_client_no_auth()
    await _post(hass, client, SAMPLE)
    s = hass.states.get("sensor.wirid_today_total")
    assert s.state == "398" and s.attributes["unit_of_measurement"] == "dhikr"
    assert s.attributes["color"] == "#34E3A0"
    data = copy.deepcopy(SAMPLE)
    data["today"].update(total=2100, tier="blue")
    await _post(hass, client, data)
    s = hass.states.get("sensor.wirid_today_total")
    assert s.state == "2100" and HEX.match(s.attributes["color"]) and s.attributes["color"] == "#3FA9FF"
    assert len(json.dumps(dict(s.attributes))) < 1024


async def test_other_fixed_sensors_have_no_color(hass, hass_client_no_auth):
    await _setup(hass)
    await _post(hass, await hass_client_no_auth(), SAMPLE)
    assert "color" not in hass.states.get("sensor.wirid_today_goal").attributes
    assert "color" in hass.states.get("sensor.wirid_subhanallah_today").attributes  # per-dhikr unchanged
