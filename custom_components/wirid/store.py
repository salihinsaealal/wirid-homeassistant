"""Persistence of the last snapshot, so sensors survive a restart."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .payload import PayloadError, Snapshot, parse, to_dict


class SnapshotStore:
    """Last snapshot of one phone."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store = Store(hass, 1, f"wirid.{entry_id}")

    async def load(self) -> Snapshot | None:
        data = await self._store.async_load()
        if not data:
            return None
        try:
            return parse(data)
        except PayloadError:
            return None

    async def save(self, s: Snapshot) -> None:
        await self._store.async_save(to_dict(s))
