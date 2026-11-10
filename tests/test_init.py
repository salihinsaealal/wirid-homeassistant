from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wirid.const import DOMAIN
from custom_components.wirid.store import SnapshotStore
from tests.test_payload import SAMPLE

WID = "abc123webhook"


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, title="Phone",
        data={"webhook_id": WID, "prefix": "wirid_", "phone_name": "Phone", "user_id": None},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_post_updates_runtime_and_store(hass, hass_client_no_auth):
    entry = await _setup(hass)
    client = await hass_client_no_auth()
    resp = await client.post(f"/api/webhook/{WID}", json=SAMPLE)
    assert resp.status == 200
    assert entry.runtime_data.snapshot.today_total == 398
    loaded = await SnapshotStore(hass, entry.entry_id).load()
    assert loaded == entry.runtime_data.snapshot


async def test_bad_posts_ignored(hass, hass_client_no_auth, caplog):
    entry = await _setup(hass)
    client = await hass_client_no_auth()
    await client.post(f"/api/webhook/{WID}", json=SAMPLE)
    good = entry.runtime_data.snapshot
    for kwargs in ({"data": "not json"}, {"json": []}, {"json": {}}):
        caplog.clear()
        resp = await client.post(f"/api/webhook/{WID}", **kwargs)
        assert resp.status == 200
        assert entry.runtime_data.snapshot is good
        assert any(r.levelname == "WARNING" for r in caplog.records)
    assert await SnapshotStore(hass, entry.entry_id).load() == good


async def test_unload_unregisters_webhook(hass, hass_client_no_auth):
    entry = await _setup(hass)
    client = await hass_client_no_auth()
    assert await hass.config_entries.async_unload(entry.entry_id)
    resp = await client.post(f"/api/webhook/{WID}", json=SAMPLE)
    assert resp.status == 200
    assert await SnapshotStore(hass, entry.entry_id).load() is None
