import copy

from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wirid.const import DOMAIN
from tests.test_payload import SAMPLE


async def _setup(hass, wid="wid1", prefix="wirid_", user_id=None, name="Phone") -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, title=name,
        data={"webhook_id": wid, "prefix": prefix, "phone_name": name, "user_id": user_id},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _post(hass, client, data, wid="wid1"):
    resp = await client.post(f"/api/webhook/{wid}", json=data)
    assert resp.status == 200
    await hass.async_block_till_done()


async def test_fixed_entities_and_ids(hass, hass_client_no_auth):
    await _setup(hass)
    assert hass.states.get("sensor.wirid_today_total").state == "unknown"
    await _post(hass, await hass_client_no_auth(), SAMPLE)
    s = hass.states.get("sensor.wirid_today_total")
    assert s.state == "398"
    assert s.attributes["unit_of_measurement"] == "dhikr"
    assert s.attributes["state_class"] == "measurement"
    assert hass.states.get("sensor.wirid_subhanallah_all_time").attributes["state_class"] == "total"
    assert hass.states.get("sensor.wirid_month_change").state == "unavailable"
    assert hass.states.get("sensor.wirid_week_change").state == "-12"
    assert hass.states.get("sensor.wirid_week_change").attributes["unit_of_measurement"] == "%"
    tier = hass.states.get("sensor.wirid_today_tier")
    assert tier.state == "emerald" and "unit_of_measurement" not in tier.attributes
    assert hass.states.get("sensor.wirid_today_dhuha").state == "388"
    ls = hass.states.get("sensor.wirid_last_session")
    assert ls.state == "60" and ls.attributes["routine"] == "Istighfar ×100"
    sent = hass.states.get("sensor.wirid_last_sent")
    assert sent.attributes["device_class"] == "timestamp"
    assert sent.state.startswith("2026-11-10T04:42:21")


async def test_device_has_all_entities(hass, hass_client_no_auth):
    entry = await _setup(hass)
    await _post(hass, await hass_client_no_auth(), SAMPLE)
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert len(devices) == 1 and devices[0].model == "Wirid for Android" and devices[0].name == "Phone"
    ents = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    assert len(ents) == 26 + 4
    assert all(e.device_id == devices[0].id for e in ents)
    assert er.async_get(hass).async_get("sensor.wirid_last_sent").entity_category == "diagnostic"


async def test_new_dhikr_added_later(hass, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    await _post(hass, client, SAMPLE)
    assert hass.states.get("sensor.wirid_doa_yunus_today") is None
    data = copy.deepcopy(SAMPLE)
    data["dhikr"]["doa_yunus"] = {"name": "Doa Yunus", "today": 7, "all_time": 70}
    await _post(hass, client, data)
    assert hass.states.get("sensor.wirid_doa_yunus_today").state == "7"
    assert hass.states.get("sensor.wirid_doa_yunus_all_time").state == "70"


async def test_missing_dhikr_keeps_all_time(hass, hass_client_no_auth):
    await _setup(hass)
    client = await hass_client_no_auth()
    await _post(hass, client, SAMPLE)
    data = copy.deepcopy(SAMPLE)
    del data["dhikr"]["subhanallah"]
    await _post(hass, client, data)
    assert hass.states.get("sensor.wirid_subhanallah_today").state == "0"
    assert hass.states.get("sensor.wirid_subhanallah_all_time").state == "4000"


async def test_friendly_name_kept(hass, hass_client_no_auth):
    await _setup(hass)
    await _post(hass, await hass_client_no_auth(), SAMPLE)
    s = hass.states.get("sensor.wirid_custom_random_1a2b_today")
    assert s.attributes["friendly_name"].endswith('Doa "ibu" é today')
    assert s.attributes["color"] == "#FF8FB1" and s.attributes["mono"] == "DI"
    assert s.attributes["slug"] == "custom_random_1a2b"


async def test_restart_restores(hass, hass_client_no_auth):
    entry = await _setup(hass)
    await _post(hass, await hass_client_no_auth(), SAMPLE)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.wirid_today_total").state == "398"
    assert hass.states.get("sensor.wirid_custom_random_1a2b_today") is not None


async def test_person_link_attributes(hass, hass_client_no_auth):
    await _setup(hass, user_id="abc")
    await _post(hass, await hass_client_no_auth(), {**SAMPLE, "app": "0.4.0"})
    a = hass.states.get("sensor.wirid_last_sent").attributes
    assert a["wirid_user_id"] == "abc" and a["wirid_prefix"] == "wirid_"
    assert a["payload_version"] == 1 and a["app_version"] == "0.4.0"


async def test_second_phone_prefix(hass, hass_client_no_auth):
    await _setup(hass)
    await _setup(hass, wid="wid2", prefix="wirid_aisyah_", name="Aisyah")
    await _post(hass, await hass_client_no_auth(), SAMPLE, wid="wid2")
    assert hass.states.get("sensor.wirid_aisyah_today_total").state == "398"
    assert hass.states.get("sensor.wirid_today_total").state == "unknown"
