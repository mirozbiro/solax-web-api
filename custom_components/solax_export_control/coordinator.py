from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SolaxApiError, SolaxEncryptedApiClient
from .const import DEFAULT_SCAN_INTERVAL


class SolaxExportCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Solax export status polling."""

    def __init__(self, hass: HomeAssistant, api: SolaxEncryptedApiClient) -> None:
        self.api = api
        super().__init__(
            hass,
            logger=hass.data["solax_export_control"]["logger"],
            name="solax_export_control",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL.total_seconds()),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            export_limit_w = await self.api.async_get_export_limit_w()
            return {"export_limit_w": export_limit_w}
        except SolaxApiError as err:
            raise UpdateFailed(str(err)) from err
