from __future__ import annotations

import asyncio

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_EXPORT_LIMIT_W, DOMAIN, WRITE_VERIFY_DELAY_SECONDS


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SolaxExportLimitNumber(entry, runtime["coordinator"], runtime["api"], runtime["min_export_w"], runtime["max_export_w"])])


class SolaxExportLimitNumber(CoordinatorEntity, NumberEntity):
    _attr_has_entity_name = True
    _attr_name = "Export Limit"
    _attr_native_step = 10
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(self, entry: ConfigEntry, coordinator, api, min_export_w: int, max_export_w: int) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._api = api
        self._command_lock = asyncio.Lock()
        self._attr_unique_id = f"{entry.unique_id}_export_limit"
        self._attr_native_min_value = min_export_w
        self._attr_native_max_value = max_export_w

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        val = data.get(ATTR_EXPORT_LIMIT_W)
        if val is None:
            return None
        return float(val)

    async def async_set_native_value(self, value: float) -> None:
        watts = int(value)
        async with self._command_lock:
            current_export_limit = (self.coordinator.data or {}).get(ATTR_EXPORT_LIMIT_W)
            if current_export_limit == watts:
                self.coordinator.logger.debug(
                    "Manual export limit request skipped; export limit already %s W",
                    watts,
                )
                return

            # Warn if trying to set 0W which some inverters don't support
            if watts == 0:
                self.coordinator.logger.warning(
                    "Setting export limit to 0 W - some inverters may not support this value. "
                    "If this fails with result=5, consider using a small positive value (e.g., 100 W)."
                )

            self.coordinator.logger.warning("Manual export limit change requested: %s W", watts)
            try:
                await self._api.async_set_export_limit_w(watts)
                await self.coordinator.async_request_refresh()
            except Exception as err:
                self.coordinator.logger.exception("Manual export limit change failed for %s W: %s", watts, err)
                raise

            current_export_limit = (self.coordinator.data or {}).get(ATTR_EXPORT_LIMIT_W)
            if current_export_limit != watts:
                await asyncio.sleep(WRITE_VERIFY_DELAY_SECONDS)
                await self.coordinator.async_request_refresh()
                current_export_limit = (self.coordinator.data or {}).get(ATTR_EXPORT_LIMIT_W)

            if current_export_limit != watts:
                self.coordinator.logger.warning(
                    "Manual export limit request for %s W completed but read-back value is %s W",
                    watts,
                    current_export_limit,
                )
