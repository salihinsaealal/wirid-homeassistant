"""The integration serves the Wirid cards: a Lovelace resource in storage mode, else an injected script."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

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
    assert add_js.call_args.args[1].startswith("/wirid_cards/wirid-cards.js?v=")


class FakeResources:
    """Stand-in for Lovelace's resource collection."""

    def __init__(self, items=None, loaded=True):
        self.items = list(items or [])
        self.loaded = loaded
        self.async_create_item = AsyncMock(side_effect=lambda d: self.items.append({"id": "new", "url": d["url"], "type": d["res_type"]}))
        self.async_update_item = AsyncMock(side_effect=self._update)
        self.async_delete_item = AsyncMock(side_effect=lambda i: self.items.__setitem__(slice(None), [x for x in self.items if x["id"] != i]))

    def _update(self, item_id, data):
        for x in self.items:
            if x["id"] == item_id:
                x.update(url=data["url"], type=data["res_type"])

    def async_items(self):
        return self.items

    async def async_get_info(self):
        self.loaded = True


def _lovelace(hass, resources, mode="storage"):
    hass.data["lovelace"] = SimpleNamespace(resource_mode=mode, resources=resources)


async def test_resource_created_in_storage_mode(hass, stub_frontend):
    res = FakeResources(loaded=False)
    _lovelace(hass, res)
    entry = _entry(hass, 1)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert len(res.items) == 1
    assert res.items[0]["url"].startswith("/wirid_cards/wirid-cards.js?v=")
    assert res.items[0]["type"] == "module"
    assert stub_frontend.call_count == 0


async def test_old_resource_updated_and_duplicates_dropped(hass, stub_frontend):
    res = FakeResources([
        {"id": "a", "url": "/wirid_cards/wirid-cards.js?v=old", "type": "module"},
        {"id": "b", "url": "/wirid_cards/wirid-cards.js", "type": "module"},
    ])
    _lovelace(hass, res)
    entry = _entry(hass, 1)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    res.async_update_item.assert_awaited_once()
    assert res.async_update_item.call_args.args[0] == "a"
    res.async_delete_item.assert_awaited_once_with("b")
    res.async_create_item.assert_not_awaited()


async def test_yaml_mode_injects_script(hass, stub_frontend):
    _lovelace(hass, FakeResources(), mode="yaml")
    entry = _entry(hass, 1)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert stub_frontend.call_count == 1


async def test_resource_removed_with_last_phone(hass, stub_frontend):
    res = FakeResources()
    _lovelace(hass, res)
    first, second = _entry(hass, 1), _entry(hass, 2)
    assert await hass.config_entries.async_setup(first.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_remove(first.entry_id)
    await hass.async_block_till_done()
    assert len(res.items) == 1  # a phone is left
    assert await hass.config_entries.async_remove(second.entry_id)
    await hass.async_block_till_done()
    assert res.items == []
