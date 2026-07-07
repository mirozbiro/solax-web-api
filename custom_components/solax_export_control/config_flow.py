from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .api import SolaxApiError, SolaxEncryptedApiClient
from .const import (
    CONF_INVERTER_SN,
    CONF_MAX_EXPORT_W,
    CONF_MIN_EXPORT_W,
    CONF_PIN,
    CONF_SN,
    CONF_TOKEN_ID,
    DEFAULT_MAX_EXPORT_W,
    DEFAULT_MIN_EXPORT_W,
    DEFAULT_NAME,
    DOMAIN,
)


class SolaxExportConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_INVERTER_SN])
            self._abort_if_unique_id_configured()

            try:
                session = async_get_clientsession(self.hass)
                api = SolaxEncryptedApiClient(
                    session=session,
                    sn=user_input[CONF_SN],
                    inverter_sn=user_input[CONF_INVERTER_SN],
                    token_id=user_input[CONF_TOKEN_ID],
                    pin=user_input.get(CONF_PIN) or None,
                )
                await api.async_get_param_init()
            except (SolaxApiError, Exception):
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_SN: user_input[CONF_SN],
                        CONF_INVERTER_SN: user_input[CONF_INVERTER_SN],
                        CONF_TOKEN_ID: user_input[CONF_TOKEN_ID],
                    },
                    options={
                        CONF_PIN: user_input.get(CONF_PIN, ""),
                        CONF_MIN_EXPORT_W: user_input.get(CONF_MIN_EXPORT_W, DEFAULT_MIN_EXPORT_W),
                        CONF_MAX_EXPORT_W: user_input.get(CONF_MAX_EXPORT_W, DEFAULT_MAX_EXPORT_W),
                    },
                )

        return self.async_show_form(step_id="user", data_schema=self._schema(), errors=errors)

    @staticmethod
    def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
        defaults = defaults or {}
        return vol.Schema(
            {
                vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
                vol.Required(CONF_SN, default=defaults.get(CONF_SN, "")): str,
                vol.Required(CONF_INVERTER_SN, default=defaults.get(CONF_INVERTER_SN, "")): str,
                vol.Required(CONF_TOKEN_ID, default=defaults.get(CONF_TOKEN_ID, "")): str,
                vol.Optional(CONF_PIN, default=defaults.get(CONF_PIN, "")): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                vol.Optional(
                    CONF_MIN_EXPORT_W, default=defaults.get(CONF_MIN_EXPORT_W, DEFAULT_MIN_EXPORT_W)
                ): vol.Coerce(int),
                vol.Optional(
                    CONF_MAX_EXPORT_W, default=defaults.get(CONF_MAX_EXPORT_W, DEFAULT_MAX_EXPORT_W)
                ): vol.Coerce(int),
            }
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return SolaxExportOptionsFlow(config_entry)


class SolaxExportOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        defaults = {
            CONF_SN: self._config_entry.options.get(CONF_SN, self._config_entry.data.get(CONF_SN, "")),
            CONF_INVERTER_SN: self._config_entry.options.get(
                CONF_INVERTER_SN,
                self._config_entry.data.get(CONF_INVERTER_SN, ""),
            ),
            CONF_TOKEN_ID: self._config_entry.options.get(
                CONF_TOKEN_ID,
                self._config_entry.data.get(CONF_TOKEN_ID, ""),
            ),
            CONF_PIN: self._config_entry.options.get(CONF_PIN, ""),
            CONF_MIN_EXPORT_W: self._config_entry.options.get(
                CONF_MIN_EXPORT_W,
                self._config_entry.data.get(CONF_MIN_EXPORT_W, DEFAULT_MIN_EXPORT_W),
            ),
            CONF_MAX_EXPORT_W: self._config_entry.options.get(
                CONF_MAX_EXPORT_W,
                self._config_entry.data.get(CONF_MAX_EXPORT_W, DEFAULT_MAX_EXPORT_W),
            ),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SN, default=defaults[CONF_SN]): str,
                    vol.Optional(CONF_INVERTER_SN, default=defaults[CONF_INVERTER_SN]): str,
                    vol.Optional(CONF_TOKEN_ID, default=defaults[CONF_TOKEN_ID]): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                    vol.Optional(CONF_PIN, default=defaults[CONF_PIN]): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                    vol.Optional(CONF_MIN_EXPORT_W, default=defaults[CONF_MIN_EXPORT_W]): vol.Coerce(int),
                    vol.Optional(CONF_MAX_EXPORT_W, default=defaults[CONF_MAX_EXPORT_W]): vol.Coerce(int),
                }
            ),
        )
