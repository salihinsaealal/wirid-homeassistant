"""Config flow (placeholder; a later task fills it in)."""

from homeassistant.config_entries import ConfigFlow

from .const import DOMAIN


class WiridConfigFlow(ConfigFlow, domain=DOMAIN):
    """Placeholder flow so the entry can load."""

    VERSION = 1
