from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_EXPORT_LIMIT_W, DOMAIN


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
        self._attr_unique_id = f"{entry.unique_id}_export_limit"
        self._attr_native_min_value = min_export_w
        self._attr_native_max_value = max_export_w

    @property
    def native_value(self) -> float | None:
        val = self.coordinator.data.get(ATTR_EXPORT_LIMIT_W)
        if val is None:
            return None
        return float(val)

    async def async_set_native_value(self, value: float) -> None:
        watts = int(value)
        self.coordinator.logger.info("Manual export limit change requested: %s W", watts)
        await self._api.async_set_export_limit_w(watts)
        await self.coordinator.async_request_refresh()
