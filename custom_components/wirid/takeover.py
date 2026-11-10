"""Taking over the entity IDs of the owner's old YAML template sensors.

The old template sensors had `unique_id: wirid_<object_id>`, so the entity registry still holds
`sensor.wirid_<object_id>` for the `template` platform after the YAML block is removed. Removing
those registry entries frees the IDs for this integration, and long-term statistics (keyed by
entity ID) carry on.
"""

from __future__ import annotations

from homeassistant.const import ATTR_RESTORED
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


def find_old(hass: HomeAssistant) -> list[er.RegistryEntry]:
    """Registry entries of the old YAML template sensors."""
    return [
        e for e in er.async_get(hass).entities.values()
        if e.platform == "template" and e.domain == "sensor" and (e.unique_id or "").startswith("wirid_")
    ]


def still_provided(hass: HomeAssistant, entries: list[er.RegistryEntry]) -> bool:
    """True while the YAML block is still loaded (a state exists that isn't a restored placeholder)."""
    for e in entries:
        state = hass.states.get(e.entity_id)
        if state is not None and not state.attributes.get(ATTR_RESTORED):
            return True
    return False


def take_over(hass: HomeAssistant, entries: list[er.RegistryEntry]) -> None:
    """Remove the old registry entries so their entity IDs are free."""
    reg = er.async_get(hass)
    for e in entries:
        if reg.async_get(e.entity_id) is not None:
            reg.async_remove(e.entity_id)
