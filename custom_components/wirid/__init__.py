"""The Wirid integration: dhikr stats from the Wirid app, one device per phone."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from aiohttp import web

from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import CONF_WEBHOOK_ID, DOMAIN, signal_update
from .payload import PayloadError, Snapshot, parse
from .store import SnapshotStore

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]


@dataclass
class WiridData:
    """Runtime state of one phone."""

    store: SnapshotStore
    snapshot: Snapshot | None


type WiridConfigEntry = ConfigEntry[WiridData]


async def async_setup_entry(hass: HomeAssistant, entry: WiridConfigEntry) -> bool:
    """Set up a phone: load its last snapshot and open its webhook."""
    store = SnapshotStore(hass, entry.entry_id)
    entry.runtime_data = WiridData(store=store, snapshot=await store.load())

    async def handle_webhook(hass: HomeAssistant, webhook_id: str, request: web.Request) -> web.Response:
        try:
            snapshot = parse(await request.json())
        except (ValueError, PayloadError, TypeError, KeyError, AttributeError) as err:
            _LOGGER.warning("Ignoring bad Wirid payload for %s: %s", entry.title, type(err).__name__)
            return web.Response(status=200)
        await entry.runtime_data.store.save(snapshot)
        entry.runtime_data.snapshot = snapshot
        async_dispatcher_send(hass, signal_update(entry.entry_id))
        return web.Response(status=200)

    webhook.async_register(
        hass, DOMAIN, entry.title, entry.data[CONF_WEBHOOK_ID], handle_webhook,
        allowed_methods={"POST"}, local_only=False,
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: WiridConfigEntry) -> bool:
    """Unload a phone."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        webhook.async_unregister(hass, entry.data[CONF_WEBHOOK_ID])
    return unloaded
