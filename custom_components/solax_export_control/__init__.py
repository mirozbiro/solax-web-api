from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SolaxEncryptedApiClient
from .const import (
    ATTR_EXPORT_LIMIT_W,
    ATTR_LAST_ERROR,
    ATTR_LAST_UPDATE_SUCCESS,
    CONF_LOG_LEVEL,
    CONF_INVERTER_SN,
    CONF_MAX_EXPORT_W,
    CONF_MIN_EXPORT_W,
    CONF_PIN,
    CONF_SN,
    CONF_TOKEN_ID,
    DEFAULT_LOG_LEVEL,
    DOMAIN,
    INTEGRATION_VERSION,
    PLATFORMS,
)
from .coordinator import SolaxExportCoordinator

_LOGGER = logging.getLogger(__name__)


def _apply_runtime_log_level(log_level_name: str) -> None:
    level = getattr(logging, log_level_name.upper(), logging.WARNING)
    integration_logger = logging.getLogger(f"custom_components.{DOMAIN}")
    integration_logger.setLevel(level)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.debug("Setting up %s integration domain", DOMAIN)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)

    options = entry.options
    sn = options.get(CONF_SN, entry.data.get(CONF_SN, ""))
    inverter_sn = options.get(CONF_INVERTER_SN, entry.data.get(CONF_INVERTER_SN, ""))
    token_id = options.get(CONF_TOKEN_ID, entry.data.get(CONF_TOKEN_ID, ""))
    pin = options.get(CONF_PIN, entry.data.get(CONF_PIN, ""))
    log_level = options.get(CONF_LOG_LEVEL, DEFAULT_LOG_LEVEL)

    _apply_runtime_log_level(log_level)

    _LOGGER.warning(
        "Solax Export Control %s initializing entry '%s' (inverter_sn=%s, sn=%s, log_level=%s)",
        INTEGRATION_VERSION,
        entry.title,
        inverter_sn,
        sn,
        log_level,
    )

    api = SolaxEncryptedApiClient(
        session=session,
        sn=sn,
        inverter_sn=inverter_sn,
        token_id=token_id,
        pin=pin,
    )

    coordinator = SolaxExportCoordinator(hass, api)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.warning(
            "Initial Solax refresh failed for entry '%s': %s. "
            "Integration will stay loaded and you can retry with the Refresh Status button.",
            entry.title,
            err,
        )
        coordinator.data = {
            ATTR_EXPORT_LIMIT_W: None,
            ATTR_LAST_UPDATE_SUCCESS: False,
            ATTR_LAST_ERROR: str(err),
        }

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "min_export_w": int(options.get(CONF_MIN_EXPORT_W, entry.data.get(CONF_MIN_EXPORT_W))),
        "max_export_w": int(options.get(CONF_MAX_EXPORT_W, entry.data.get(CONF_MAX_EXPORT_W))),
    }

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.warning("Solax Export Control %s setup completed for entry '%s'", INTEGRATION_VERSION, entry.title)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.warning("Solax Export Control %s unloading entry '%s'", INTEGRATION_VERSION, entry.title)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
