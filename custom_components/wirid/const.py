"""Constants for the Wirid integration."""

DOMAIN = "wirid"

CONF_WEBHOOK_ID = "webhook_id"
CONF_USER_ID = "user_id"
CONF_PREFIX = "prefix"
CONF_PHONE_NAME = "phone_name"
# {object_id: entity_id} of old YAML sensors this phone took over (their IDs came from their names).
CONF_ENTITY_IDS = "entity_ids"

# The nine waktu, in the order the app's payload and the old YAML list them.
WAKTU = ("subuh", "syuruk", "dhuha", "zawal", "zohor", "asar", "maghrib", "isyak", "tahajjud")
WAKTU_NAMES = {
    "subuh": "Subuh", "syuruk": "Syuruk", "dhuha": "Dhuha", "zawal": "Zawal", "zohor": "Zohor",
    "asar": "Asar", "maghrib": "Maghrib", "isyak": "Isyak", "tahajjud": "Tahajjud",
}


def signal_update(entry_id: str) -> str:
    """Dispatcher signal fired when a phone's snapshot changes."""
    return f"wirid_update_{entry_id}"


def signal_new_dhikr(entry_id: str) -> str:
    """Dispatcher signal fired when a phone sends a dhikr not seen before."""
    return f"wirid_new_dhikr_{entry_id}"
