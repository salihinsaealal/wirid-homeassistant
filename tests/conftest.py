"""Shared fixtures."""

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockModule, mock_integration


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load custom_components/wirid in every test."""
    yield


@pytest.fixture(autouse=True)
def stub_frontend(hass):
    """Stand in for HA's frontend (its hass_frontend package isn't in the test env); yields add_extra_js_url."""
    mock_integration(hass, MockModule("frontend"))
    with patch("custom_components.wirid.cards.add_extra_js_url") as add_js:
        yield add_js
