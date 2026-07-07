from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SolaxEncryptedApiClient
from .const import (
    CONF_INVERTER_SN,
    CONF_MAX_EXPORT_W,
    CONF_MIN_EXPORT_W,
    CONF_PIN,
    CONF_SN,
    CONF_TOKEN_ID,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import SolaxExportCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["logger"] = _LOGGER
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)

    options = entry.options
    pin = options.get(CONF_PIN, entry.data.get(CONF_PIN, ""))

    api = SolaxEncryptedApiClient(
        session=session,
        sn=entry.data[CONF_SN],
        inverter_sn=entry.data[CONF_INVERTER_SN],
        token_id=entry.data[CONF_TOKEN_ID],
        pin=pin,
    )

    coordinator = SolaxExportCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "min_export_w": options.get(CONF_MIN_EXPORT_W, entry.data.get(CONF_MIN_EXPORT_W)),
        "max_export_w": options.get(CONF_MAX_EXPORT_W, entry.data.get(CONF_MAX_EXPORT_W)),
    }

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
