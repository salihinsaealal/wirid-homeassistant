"""Base entity: one device per phone, entity ids fixed by the phone's prefix."""

from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import CONF_ENTITY_IDS, CONF_PHONE_NAME, CONF_PREFIX, DOMAIN, signal_update
from .naming import entity_id_for


class WiridEntity(Entity):
    """A Wirid sensor of one phone, refreshed whenever its snapshot changes."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry, object_id: str, name: str) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{object_id}"
        self._attr_name = name
        self.entity_id = self.entity_id_of(object_id)

    def entity_id_of(self, object_id: str) -> str:
        """The entity ID this phone gives an object id (a taken-over old ID when there is one)."""
        return entity_id_for(self._entry.data[CONF_PREFIX], object_id, self._entry.data.get(CONF_ENTITY_IDS))

    @property
    def snapshot(self):
        return self._entry.runtime_data.snapshot

    @property
    def device_info(self) -> DeviceInfo:
        snap = self.snapshot
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.data[CONF_PHONE_NAME],
            manufacturer="Wirid",
            model="Wirid for Android",
            sw_version=snap.app if snap else None,
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(self.hass, signal_update(self._entry.entry_id), self._refresh)
        )
        self._update_from_snapshot()

    @callback
    def _refresh(self) -> None:
        """Re-read the snapshot into the entity's attributes, then write state."""
        self._update_from_snapshot()
        self.async_write_ha_state()

    def _update_from_snapshot(self) -> None:
        raise NotImplementedError
