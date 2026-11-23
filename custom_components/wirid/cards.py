"""Serve the Wirid dashboard cards and register them as a Lovelace resource.

A Lovelace resource is loaded by the dashboard before it builds the cards, so the cards
are defined in time on every client. add_extra_js_url (the old way) races the dashboard:
on slower clients (the Companion app, phone browsers) the cards were not defined yet and
showed "Configuration error". It is kept only as a fallback for YAML-mode resources.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from pathlib import Path
from typing import Any

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_HERE = Path(__file__).parent
CARDS_URL = "/wirid_cards"
CARDS_FILE = f"{CARDS_URL}/wirid-cards.js"

_URL = f"{DOMAIN}_cards_url"
_INJECTED = f"{DOMAIN}_cards_injected"
_LOCK = f"{DOMAIN}_cards_lock"


def _digest() -> str:
    """Hash of both card files, so any change busts browser caches."""
    h = hashlib.sha256()
    for name in ("wirid-cards.js", "wirid-core.js"):
        h.update((_HERE / "frontend" / name).read_bytes())
    return h.hexdigest()[:8]


def _lovelace(hass: HomeAssistant) -> tuple[str | None, Any]:
    """(resource mode, resource collection) across Home Assistant versions."""
    data = hass.data.get("lovelace")
    if data is None:
        return None, None
    if isinstance(data, dict):
        return data.get("mode"), data.get("resources")
    mode = getattr(data, "resource_mode", None) or getattr(data, "mode", None)
    return mode, getattr(data, "resources", None)


def _ours(resources: Any) -> list[dict[str, Any]]:
    return [r for r in (resources.async_items() or []) if str(r.get("url", "")).split("?", 1)[0] == CARDS_FILE]


async def async_register_cards(hass: HomeAssistant) -> None:
    """Serve frontend/ once, then make sure the dashboard resource exists and is current."""
    async with hass.data.setdefault(_LOCK, asyncio.Lock()):
        url = hass.data.get(_URL)
        if url is None:
            await hass.http.async_register_static_paths(
                [StaticPathConfig(CARDS_URL, str(_HERE / "frontend"), cache_headers=False)]
            )
            url = f"{CARDS_FILE}?v={await hass.async_add_executor_job(_digest)}"
            hass.data[_URL] = url

        mode, resources = _lovelace(hass)
        if mode == "storage" and resources is not None:
            try:
                if not getattr(resources, "loaded", True):
                    await resources.async_get_info()  # load the store, or we'd add a duplicate
                ours = _ours(resources)
                if not ours:
                    await resources.async_create_item({"res_type": "module", "url": url})
                else:
                    if ours[0].get("url") != url:
                        await resources.async_update_item(ours[0]["id"], {"res_type": "module", "url": url})
                    for extra in ours[1:]:
                        await resources.async_delete_item(extra["id"])
                return
            except Exception:  # noqa: BLE001 - never let the cards break setup
                _LOGGER.warning("Could not add the Wirid cards as a dashboard resource", exc_info=True)

        if not hass.data.get(_INJECTED):
            hass.data[_INJECTED] = True
            add_extra_js_url(hass, url)


async def async_unregister_cards(hass: HomeAssistant) -> None:
    """Remove the dashboard resource (when the last phone is deleted)."""
    mode, resources = _lovelace(hass)
    if mode != "storage" or resources is None:
        return
    try:
        if not getattr(resources, "loaded", True):
            await resources.async_get_info()
        for item in _ours(resources):
            await resources.async_delete_item(item["id"])
    except Exception:  # noqa: BLE001
        _LOGGER.debug("Could not remove the Wirid cards resource", exc_info=True)
