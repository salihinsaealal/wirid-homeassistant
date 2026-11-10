"""Config flow: one entry per phone, linked to a person, with its own webhook."""

from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.network import NoURLAvailableError
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .const import CONF_PHONE_NAME, CONF_PREFIX, CONF_USER_ID, CONF_WEBHOOK_ID, DOMAIN
from .naming import prefix_for
from .takeover import find_old, still_provided, take_over

NOBODY = "nobody"
CHOICE = "choice"
TAKE_OVER = "take_over"
START_FRESH = "start_fresh"
CONF_URL = "url"


def webhook_url(hass: HomeAssistant, webhook_id: str) -> str:
    """The phone's webhook URL: external when set, else internal; just the path if HA knows neither."""
    try:
        return webhook.async_generate_url(hass, webhook_id, prefer_external=True)
    except NoURLAvailableError:
        return webhook.async_generate_path(webhook_id)


def _placeholders(hass: HomeAssistant, webhook_id: str) -> dict[str, str]:
    # No wirid:// "open in Wirid" link: HA's markdown sanitiser (js-xss) empties any href that
    # isn't http(s), mailto, tel, ftp, relative or #, so it would render dead. Copy only (README).
    return {"url": webhook_url(hass, webhook_id)}


def _url_schema(url: str) -> vol.Schema:
    """A prefilled text field, so the URL can be selected and copied."""
    return vol.Schema({vol.Optional(CONF_URL, description={"suggested_value": url}): TextSelector()})


async def _person_schema(hass: HomeAssistant, current: str | None) -> vol.Schema:
    users = [u for u in await hass.auth.async_get_users() if u.is_active and not u.system_generated]
    options = [SelectOptionDict(value=NOBODY, label="Nobody")]
    options += [SelectOptionDict(value=u.id, label=u.name or u.id) for u in sorted(users, key=lambda u: u.name or "")]
    return vol.Schema({
        vol.Required(CONF_USER_ID, default=current or NOBODY): SelectSelector(
            SelectSelectorConfig(options=options, mode=SelectSelectorMode.LIST, translation_key="person")
        ),
    })


def _user_id(value: str) -> str | None:
    return None if value == NOBODY else value


class WiridConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a phone: name → person → (take over old sensors) → done."""

    VERSION = 1

    def __init__(self) -> None:
        self._webhook_id: str | None = None
        self._name = ""
        self._prefix = ""
        self._user_id: str | None = None
        self._take_over = False

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return WiridOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input[CONF_PHONE_NAME].strip()
            if name:
                self._name = name
                taken = {e.data.get(CONF_PREFIX) for e in self._async_current_entries(include_ignore=False)}
                self._prefix = prefix_for(name, {t for t in taken if t})
                return await self.async_step_person()
            errors[CONF_PHONE_NAME] = "name_required"
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_PHONE_NAME): str}),
            errors=errors,
        )

    async def async_step_person(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None and CONF_USER_ID in user_input:
            self._user_id = _user_id(user_input[CONF_USER_ID])
            if self._prefix == "wirid_" and find_old(self.hass):
                return await self.async_step_takeover()
            return await self.async_step_done()
        return self.async_show_form(
            step_id="person", data_schema=await _person_schema(self.hass, None),
            description_placeholders={"phone": self._name},
        )

    async def async_step_takeover(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        old = find_old(self.hass)
        if not old:
            return await self.async_step_done()
        errors: dict[str, str] = {}
        if still_provided(self.hass, old):
            errors["base"] = "yaml_still_loaded"
        # While the YAML block is still loaded, neither choice proceeds: taking over would be undone
        # by a template reload, and starting fresh would put _2 sensors beside the live old ones.
        if user_input is not None and not errors:
            self._take_over = user_input[CHOICE] == TAKE_OVER
            return await self.async_step_done()
        return self.async_show_form(
            step_id="takeover",
            data_schema=vol.Schema({
                vol.Required(CHOICE, default=TAKE_OVER): SelectSelector(
                    SelectSelectorConfig(
                        options=[TAKE_OVER, START_FRESH], mode=SelectSelectorMode.LIST, translation_key="takeover",
                    )
                ),
            }),
            errors=errors,
            description_placeholders={"count": str(len(old))},
        )

    async def async_step_done(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._webhook_id is None:
            self._webhook_id = webhook.async_generate_id()
        if user_input is not None:
            if self._take_over:
                # Only now, as the entry is created: an abandoned flow removes nothing.
                take_over(self.hass, find_old(self.hass))
            return self.async_create_entry(
                title=self._name,
                data={
                    CONF_WEBHOOK_ID: self._webhook_id,
                    CONF_PREFIX: self._prefix,
                    CONF_PHONE_NAME: self._name,
                    CONF_USER_ID: self._user_id,
                },
            )
        placeholders = _placeholders(self.hass, self._webhook_id)
        return self.async_show_form(
            step_id="done", data_schema=_url_schema(placeholders["url"]), description_placeholders=placeholders,
        )


class WiridOptionsFlow(OptionsFlow):
    """Change the person, show the address again, or give the phone a new address."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(step_id="init", menu_options=["person", "address", "new_address"])

    async def async_step_person(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self.config_entry
        if user_input is not None:
            data = {**entry.data, CONF_USER_ID: _user_id(user_input[CONF_USER_ID])}
            self.hass.config_entries.async_update_entry(entry, data=data)
            self.hass.config_entries.async_schedule_reload(entry.entry_id)
            return self.async_create_entry(data=dict(entry.options))
        return self.async_show_form(
            step_id="person", data_schema=await _person_schema(self.hass, entry.data.get(CONF_USER_ID)),
            description_placeholders={"phone": entry.data[CONF_PHONE_NAME]},
        )

    async def async_step_address(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=dict(self.config_entry.options))
        placeholders = _placeholders(self.hass, self.config_entry.data[CONF_WEBHOOK_ID])
        return self.async_show_form(
            step_id="address", data_schema=_url_schema(placeholders["url"]), description_placeholders=placeholders,
        )

    async def async_step_new_address(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self.config_entry
        if user_input is not None:
            data = {**entry.data, CONF_WEBHOOK_ID: webhook.async_generate_id()}
            self.hass.config_entries.async_update_entry(entry, data=data)
            self.hass.config_entries.async_schedule_reload(entry.entry_id)
            return await self.async_step_address()
        return self.async_show_form(
            step_id="new_address", data_schema=vol.Schema({}),
            description_placeholders={"phone": entry.data[CONF_PHONE_NAME]},
        )
