"""Taking over the owner's old YAML template sensors."""

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er

from custom_components.wirid.const import DOMAIN
from custom_components.wirid.takeover import find_old, still_provided
from tests.test_payload import SAMPLE

OLD = ("today_total", "subhanallah_all_time")


def _seed(hass, live: bool = False) -> None:
    reg = er.async_get(hass)
    for oid in OLD:
        e = reg.async_get_or_create("sensor", "template", f"wirid_{oid}", suggested_object_id=f"wirid_{oid}")
        assert e.entity_id == f"sensor.wirid_{oid}"
        if live:
            hass.states.async_set(e.entity_id, "5")
        else:
            e.write_unavailable_state(hass)
    # Unrelated template sensor: never touched.
    reg.async_get_or_create("sensor", "template", "other_thing", suggested_object_id="other_thing")


async def _to_takeover(hass):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"phone_name": "Phone"})
    return await hass.config_entries.flow.async_configure(result["flow_id"], {"user_id": "nobody"})


async def _finish(hass, result):
    assert result["step_id"] == "done"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    return result


async def _post(hass, client, wid):
    resp = await client.post(f"/api/webhook/{wid}", json=SAMPLE)
    assert resp.status == 200
    await hass.async_block_till_done()


async def test_find_old_and_still_provided(hass):
    _seed(hass)
    old = find_old(hass)
    assert sorted(e.entity_id for e in old) == [f"sensor.wirid_{o}" for o in sorted(OLD)]
    assert not still_provided(hass, old)
    hass.states.async_set("sensor.wirid_today_total", "5")
    assert still_provided(hass, old)


async def test_takeover_offered_and_applied(hass, hass_client_no_auth):
    _seed(hass)
    result = await _to_takeover(hass)
    assert result["step_id"] == "takeover"
    assert result["description_placeholders"]["count"] == "2"
    assert not result["errors"]
    # Nothing removed before the entry is created.
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"choice": "take_over"})
    assert len(find_old(hass)) == 2
    result = await _finish(hass, result)
    reg = er.async_get(hass)
    assert find_old(hass) == []
    assert reg.async_get("sensor.other_thing") is not None
    await _post(hass, await hass_client_no_auth(), result["data"]["webhook_id"])
    assert reg.async_get("sensor.wirid_today_total").platform == DOMAIN
    assert reg.async_get("sensor.wirid_subhanallah_all_time").platform == DOMAIN
    assert hass.states.get("sensor.wirid_today_total").state == "398"
    assert reg.async_get("sensor.wirid_today_total_2") is None
    assert hass.states.get("sensor.wirid_today_total_2") is None


async def test_takeover_blocked_while_yaml_loaded(hass):
    _seed(hass, live=True)
    result = await _to_takeover(hass)
    assert result["step_id"] == "takeover"
    assert result["errors"] == {"base": "yaml_still_loaded"}
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"choice": "take_over"})
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "takeover"
    assert result["errors"] == {"base": "yaml_still_loaded"}
    assert hass.config_entries.async_entries(DOMAIN) == []
    assert len(find_old(hass)) == 2


async def test_abandoned_flow_removes_nothing(hass):
    _seed(hass)
    result = await _to_takeover(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"choice": "take_over"})
    hass.config_entries.flow.async_abort(result["flow_id"])
    assert len(find_old(hass)) == 2


async def test_start_fresh_keeps_old(hass, hass_client_no_auth):
    _seed(hass)
    result = await _to_takeover(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"choice": "start_fresh"})
    result = await _finish(hass, result)
    reg = er.async_get(hass)
    assert len(find_old(hass)) == 2
    assert reg.async_get("sensor.wirid_today_total").platform == "template"
    await _post(hass, await hass_client_no_auth(), result["data"]["webhook_id"])
    assert reg.async_get("sensor.wirid_today_total_2").platform == DOMAIN
    assert hass.states.get("sensor.wirid_today_total_2").state == "398"


async def test_second_phone_never_offered_takeover(hass):
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    MockConfigEntry(
        domain=DOMAIN, title="Mine",
        data={"webhook_id": "w1", "prefix": "wirid_", "phone_name": "Mine", "user_id": None},
    ).add_to_hass(hass)
    _seed(hass)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"phone_name": "Aisyah"})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"user_id": "nobody"})
    assert result["step_id"] == "done"


async def test_start_fresh_refused_while_yaml_loaded(hass):
    _seed(hass, live=True)
    result = await _to_takeover(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"choice": "start_fresh"})
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "takeover"
    assert result["errors"] == {"base": "yaml_still_loaded"}
    assert hass.config_entries.async_entries(DOMAIN) == []
    assert len(find_old(hass)) == 2
    assert all(e.platform == "template" for e in find_old(hass))
