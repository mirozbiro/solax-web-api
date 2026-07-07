from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SolaxApiError, SolaxEncryptedApiClient
from .const import ATTR_EXPORT_LIMIT_W, ATTR_LAST_ERROR, ATTR_LAST_UPDATE_SUCCESS, DEFAULT_SCAN_INTERVAL


class SolaxExportCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Solax export status polling."""

    def __init__(self, hass: HomeAssistant, api: SolaxEncryptedApiClient) -> None:
        self.api = api
        self.last_error: str | None = None
        super().__init__(
            hass,
            logger=hass.data["solax_export_control"]["logger"],
            name="solax_export_control",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL.total_seconds()),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            self.logger.debug("Refreshing Solax export status")
            export_limit_w = await self.api.async_get_export_limit_w()
            self.last_error = None
            self.logger.debug("Solax export status refresh succeeded with export limit %s W", export_limit_w)
            return {
                ATTR_EXPORT_LIMIT_W: export_limit_w,
                ATTR_LAST_UPDATE_SUCCESS: True,
                ATTR_LAST_ERROR: None,
            }
        except SolaxApiError as err:
            self.last_error = str(err)
            self.logger.error("Solax export status refresh failed: %s", err)
            raise UpdateFailed(str(err)) from err
