from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_EXPORT_LIMIT_W, DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        SolaxExportPresetSwitch(
            entry,
            runtime["coordinator"],
            runtime["api"],
            runtime["min_export_w"],
            runtime["max_export_w"],
        )
    ])


class SolaxExportPresetSwitch(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True
    _attr_name = "Export Preset"
    _attr_icon = "mdi:swap-horizontal"

    def __init__(self, entry: ConfigEntry, coordinator, api, min_export_w: int, max_export_w: int) -> None:
        super().__init__(coordinator)
        self._api = api
        self._min_export_w = int(min_export_w)
        self._max_export_w = int(max_export_w)
        self._attr_unique_id = f"{entry.unique_id}_export_preset"

    @property
    def available(self) -> bool:
        return self.coordinator.data is not None

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        return data.get(ATTR_EXPORT_LIMIT_W) == self._max_export_w

    async def async_turn_on(self, **kwargs) -> None:
        self.coordinator.logger.info("Preset switch set to max export: %s W", self._max_export_w)
        await self._api.async_set_export_limit_w(self._max_export_w)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        self.coordinator.logger.info("Preset switch set to min export: %s W", self._min_export_w)
        await self._api.async_set_export_limit_w(self._min_export_w)
        await self.coordinator.async_request_refresh()