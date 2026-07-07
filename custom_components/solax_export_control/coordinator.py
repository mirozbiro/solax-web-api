from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SolaxApiError, SolaxEncryptedApiClient
from .const import ATTR_EXPORT_LIMIT_W, ATTR_LAST_ERROR, ATTR_LAST_UPDATE_SUCCESS, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class SolaxExportCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Solax export status polling."""

    def __init__(self, hass: HomeAssistant, api: SolaxEncryptedApiClient) -> None:
        self.api = api
        self.last_error: str | None = None
        super().__init__(
            hass,
            logger=_LOGGER,
            name="solax_export_control",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL.total_seconds()),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            self.logger.debug("Refreshing Solax export status")
            export_limit_w = await self.api.async_get_export_limit_w()
            if export_limit_w is None:
                self.last_error = "Export register not found or unreadable from paramInit response"
                self.logger.warning("Solax refresh completed but export limit is unknown")
            else:
                self.last_error = None
            self.logger.debug("Solax export status refresh succeeded with export limit %s W", export_limit_w)
            return {
                ATTR_EXPORT_LIMIT_W: export_limit_w,
                ATTR_LAST_UPDATE_SUCCESS: export_limit_w is not None,
                ATTR_LAST_ERROR: self.last_error,
            }
        except SolaxApiError as err:
            self.last_error = str(err)
            self.logger.error("Solax export status refresh failed: %s", err)
            raise UpdateFailed(str(err)) from err
        except Exception as err:  # pragma: no cover - defensive path
            self.last_error = str(err)
            self.logger.exception("Unexpected Solax refresh failure")
            raise UpdateFailed(str(err)) from err
