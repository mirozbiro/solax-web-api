from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SolaxManualRefreshButton(entry, runtime["coordinator"])])


class SolaxManualRefreshButton(CoordinatorEntity, ButtonEntity):
    _attr_has_entity_name = True
    _attr_name = "Refresh Status"

    def __init__(self, entry: ConfigEntry, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.unique_id}_refresh_status"

    async def async_press(self) -> None:
        self.coordinator.logger.warning("Manual Solax status refresh requested from button")
        try:
            await self.coordinator.async_request_refresh()
            self.coordinator.logger.warning("Manual Solax status refresh completed")
        except Exception as err:
            self.coordinator.logger.exception("Manual Solax status refresh failed: %s", err)
            raise
