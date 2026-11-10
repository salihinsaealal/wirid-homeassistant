"""The config flow and options flow."""

from homeassistant import config_entries
from homeassistant.core_config import async_process_ha_core_config
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry, MockUser

from custom_components.wirid.const import DOMAIN
from tests.test_payload import SAMPLE

NOBODY = "nobody"


async def _start(hass, name="Phone"):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "user"
    return await hass.config_entries.flow.async_configure(result["flow_id"], {"phone_name": name})


def _person_options(result) -> dict[str, str]:
    schema = result["data_schema"].schema
    selector = next(v for k, v in schema.items() if str(k) == "user_id")
    return {o["value"]: o["label"] for o in selector.config["options"]}


async def test_full_flow_first_phone(hass):
    result = await _start(hass)
    assert result["step_id"] == "person"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"user_id": NOBODY})
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "done"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Phone"
    data = result["data"]
    assert data["prefix"] == "wirid_"
    assert data["phone_name"] == "Phone"
    assert len(data["webhook_id"]) >= 32


async def test_second_phone_prefix(hass):
    MockConfigEntry(
        domain=DOMAIN, title="Mine",
        data={"webhook_id": "w1", "prefix": "wirid_", "phone_name": "Mine", "user_id": None},
    ).add_to_hass(hass)
    result = await _start(hass, "Aisyah")
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"user_id": NOBODY})
    assert result["step_id"] == "done"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["data"]["prefix"] == "wirid_aisyah_"


async def test_person_choices_exclude_system_users(hass, hass_admin_user):
    MockUser(name="Aisyah").add_to_hass(hass)
    MockUser(name="Bot", system_generated=True).add_to_hass(hass)
    MockUser(name="Gone", is_active=False).add_to_hass(hass)
    result = await _start(hass)
    labels = set(_person_options(result).values())
    assert "Aisyah" in labels and hass_admin_user.name in labels
    assert "Bot" not in labels and "Gone" not in labels
    assert _person_options(result)[NOBODY] == "Nobody"


async def test_person_link_stored(hass):
    user = MockUser(name="Aisyah").add_to_hass(hass)
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"user_id": user.id})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["data"]["user_id"] == user.id


async def test_nobody_stores_none(hass):
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"user_id": NOBODY})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["data"]["user_id"] is None


async def test_done_shows_external_url(hass):
    await async_process_ha_core_config(
        hass, {"internal_url": "http://192.168.1.5:8123", "external_url": "https://ha.example.com"}
    )
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"user_id": NOBODY})
    url = result["description_placeholders"]["url"]
    assert url.startswith("https://ha.example.com/api/webhook/")
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert url.endswith(result["data"]["webhook_id"])


async def test_done_falls_back_to_internal_url(hass):
    await async_process_ha_core_config(hass, {"internal_url": "http://192.168.1.5:8123"})
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"user_id": NOBODY})
    assert result["description_placeholders"]["url"].startswith("http://192.168.1.5:8123/api/webhook/")


async def _entry(hass, user_id=None) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, title="Phone",
        data={"webhook_id": "w" * 32, "prefix": "wirid_", "phone_name": "Phone", "user_id": user_id},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_options_menu(hass):
    entry = await _entry(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert set(result["menu_options"]) == {"person", "address", "new_address"}


async def test_options_change_person(hass, hass_client_no_auth):
    user = MockUser(name="Aisyah").add_to_hass(hass)
    entry = await _entry(hass)
    await (await hass_client_no_auth()).post(f"/api/webhook/{'w' * 32}", json=SAMPLE)
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "person"})
    assert result["step_id"] == "person"
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"user_id": user.id})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.data["user_id"] == user.id
    assert hass.states.get("sensor.wirid_last_sent").attributes["wirid_user_id"] == user.id


async def test_options_address_shows_url(hass):
    entry = await _entry(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "address"})
    assert result["step_id"] == "address"
    assert result["description_placeholders"]["url"].endswith("/api/webhook/" + "w" * 32)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.data["webhook_id"] == "w" * 32


async def test_options_new_address(hass, hass_client_no_auth):
    entry = await _entry(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "new_address"})
    assert result["step_id"] == "new_address"
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()
    new_id = entry.data["webhook_id"]
    assert new_id != "w" * 32 and len(new_id) >= 32
    assert result["step_id"] == "address"
    assert result["description_placeholders"]["url"].endswith(new_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    client = await hass_client_no_auth()
    await client.post(f"/api/webhook/{'w' * 32}", json=SAMPLE)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.wirid_today_total").state == "unknown"
    await client.post(f"/api/webhook/{new_id}", json=SAMPLE)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.wirid_today_total").state == "398"


async def test_blank_name_rejected(hass):
    result = await _start(hass, "   ")
    assert result["step_id"] == "user"
    assert result["errors"] == {"phone_name": "name_required"}


async def test_webhook_id_kept_across_steps(hass):
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"user_id": NOBODY})
    url = result["description_placeholders"]["url"]
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert url.endswith("/api/webhook/" + result["data"]["webhook_id"])
