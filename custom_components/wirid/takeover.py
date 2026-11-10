"""Taking over the entity IDs of the owner's old YAML template sensors.

The old template sensors had `unique_id: wirid_<object_id>`, but the template platform derived each
entity ID from the sensor's name ("Wirid Allahu Akbar all time" → `sensor.wirid_allahu_akbar_all_time`
for unique_id `wirid_allahuakbar_all_time`), and the owner may have renamed some. So the takeover
records each old entry's actual entity ID by object id, then removes the entries; the integration's
entities reuse those exact IDs, and long-term statistics (keyed by entity ID) carry on.
"""

from __future__ import annotations

from homeassistant.const import ATTR_RESTORED
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


OLD_PREFIX = "wirid_"


def find_old(hass: HomeAssistant) -> list[er.RegistryEntry]:
    """Registry entries of the old YAML template sensors."""
    return [
        e for e in er.async_get(hass).entities.values()
        if e.platform == "template" and e.domain == "sensor" and (e.unique_id or "").startswith(OLD_PREFIX)
    ]


def still_provided(hass: HomeAssistant, entries: list[er.RegistryEntry]) -> bool:
    """True while the YAML block is still loaded (a state exists that isn't a restored placeholder)."""
    for e in entries:
        state = hass.states.get(e.entity_id)
        if state is not None and not state.attributes.get(ATTR_RESTORED):
            return True
    return False


def entity_id_map(entries: list[er.RegistryEntry]) -> dict[str, str]:
    """{object_id: entity_id} of the old entries (unique_id `wirid_<object_id>`)."""
    return {e.unique_id.removeprefix(OLD_PREFIX): e.entity_id for e in entries}


def take_over(hass: HomeAssistant, entries: list[er.RegistryEntry]) -> dict[str, str]:
    """Record the old entity IDs, then remove their registry entries so the IDs are free."""
    taken = entity_id_map(entries)
    reg = er.async_get(hass)
    for e in entries:
        if reg.async_get(e.entity_id) is not None:
            reg.async_remove(e.entity_id)
    return taken
