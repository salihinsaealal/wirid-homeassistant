"""The integration serves the Wirid cards and loads them into the frontend once."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wirid.const import DOMAIN


def _entry(hass, n: int) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, title=f"Phone {n}",
        data={"webhook_id": f"hook{n}", "prefix": "wirid_" if n == 1 else f"wirid_p{n}_",
              "phone_name": f"Phone {n}", "user_id": None},
    )
    entry.add_to_hass(hass)
    return entry


async def test_cards_js_served(hass, hass_client):
    entry = _entry(hass, 1)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    resp = await (await hass_client()).get("/wirid_cards/wirid-cards.js")
    assert resp.status == 200
    assert "Wirid cards" in await resp.text()


async def test_js_url_added_once(hass, stub_frontend):
    add_js = stub_frontend
    first, second = _entry(hass, 1), _entry(hass, 2)
    assert await hass.config_entries.async_setup(first.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_reload(first.entry_id)
    await hass.async_block_till_done()
    assert second.state.value == "loaded"
    assert add_js.call_count == 1
    assert add_js.call_args.args[1].startswith("/wirid_cards/wirid-cards.js?v=0.3.0")
