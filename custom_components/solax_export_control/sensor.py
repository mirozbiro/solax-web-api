from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_EXPORT_LIMIT_W, ATTR_LAST_ERROR, ATTR_LAST_UPDATE_SUCCESS, DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SolaxExportLimitSensor(entry, runtime["coordinator"])])


class SolaxExportLimitSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Current Export Limit"
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(self, entry: ConfigEntry, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.unique_id}_current_export_limit"

    @property
    def native_value(self):
        return self.coordinator.data.get(ATTR_EXPORT_LIMIT_W)

    @property
    def extra_state_attributes(self):
        return {
            ATTR_LAST_UPDATE_SUCCESS: self.coordinator.data.get(ATTR_LAST_UPDATE_SUCCESS),
            ATTR_LAST_ERROR: self.coordinator.data.get(ATTR_LAST_ERROR),
        }
