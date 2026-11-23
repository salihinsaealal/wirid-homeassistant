"""Serve the Wirid dashboard cards and load them into every dashboard."""

from __future__ import annotations

import json
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_HERE = Path(__file__).parent
VERSION = json.loads((_HERE / "manifest.json").read_text(encoding="utf-8"))["version"]
CARDS_URL = "/wirid_cards"
# The version busts browser caches when the integration updates.
CARDS_JS = f"{CARDS_URL}/wirid-cards.js?v={VERSION}"
_DONE = f"{DOMAIN}_cards"


async def async_register_cards(hass: HomeAssistant) -> None:
    """Serve frontend/ and add the cards' module to the frontend, once per Home Assistant run."""
    if hass.data.get(_DONE):
        return
    hass.data[_DONE] = True
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARDS_URL, str(_HERE / "frontend"), cache_headers=False)]
    )
    add_extra_js_url(hass, CARDS_JS)
