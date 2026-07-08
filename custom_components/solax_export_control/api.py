import base64
import json
import logging
import time
import uuid
from collections import OrderedDict
from typing import Any
from urllib.parse import quote

import aiohttp
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from .const import PARAMINIT_EXPORT_LIMIT_INDEX, REG_EXPORT_LIMIT, REG_PIN

_LOGGER = logging.getLogger(__name__)


class SolaxApiError(Exception):
    """Solax API error."""


class SolaxEncryptedApiClient:
    """Client for Solax encrypted web API endpoints."""

    BASE_URL = "https://euapi.solaxcloud.com"
    AES_KEY = "hj7x22H$yuBI0456"
    AES_IV = "NIfb&74GUY86Gfgh"

    def __init__(
        self,
        session: aiohttp.ClientSession,
        sn: str,
        inverter_sn: str,
        token_id: str,
        pin: str | None = None,
    ) -> None:
        self._session = session
        self._sn = sn
        self._inverter_sn = inverter_sn
        self._token_id = token_id
        self._pin = pin

    def update_pin(self, pin: str | None) -> None:
        self._pin = pin

    def _serialize_params(self, params: OrderedDict[str, Any]) -> str:
        parts: list[str] = []
        for key, value in params.items():
            encoded_key = quote(str(key), safe="")
            encoded_val = quote(str(value), safe="")
            parts.append(f"{encoded_key}={encoded_val}")
        return "&".join(parts)

    def _encrypt(self, plain: str) -> str:
        plaintext = plain.encode("utf-8")
        padded = pad(plaintext, AES.block_size)
        cipher = AES.new(self.AES_KEY.encode("utf-8"), AES.MODE_CBC, self.AES_IV.encode("utf-8"))
        return base64.b64encode(cipher.encrypt(padded)).decode("ascii")

    def _decrypt(self, payload_b64: str) -> str:
        raw = base64.b64decode(payload_b64)
        cipher = AES.new(self.AES_KEY.encode("utf-8"), AES.MODE_CBC, self.AES_IV.encode("utf-8"))
        padded = cipher.decrypt(raw)
        return unpad(padded, AES.block_size).decode("utf-8")

    def _encrypt_payload(self, params: OrderedDict[str, Any]) -> str:
        return self._encrypt(self._serialize_params(params))

    def _build_query_payload(self) -> str:
        query_params = OrderedDict(
            [
                ("timeStamp", int(time.time() * 1000)),
                ("requestId", uuid.uuid4().hex),
            ]
        )
        return self._encrypt_payload(query_params)

    def _base_headers(self) -> dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://global.solaxcloud.com/",
            "Content-Type": "application/x-www-form-urlencoded",
            "websiteType": "0",
            "appVer": "V7.5.0",
            "crytoVer": "1",
            "Origin": "https://global.solaxcloud.com",
        }

    async def _post_encrypted(self, path: str, data_payload: OrderedDict[str, Any]) -> dict[str, Any]:
        _LOGGER.debug("Posting encrypted Solax request to %s for inverter %s", path, self._inverter_sn)
        encrypted_body = self._encrypt_payload(data_payload)
        encrypted_query = self._build_query_payload()
        full_url = f"{self.BASE_URL}{path}?data={quote(encrypted_query, safe='')}"

        body = {"data": encrypted_body}
        async with self._session.post(
            full_url,
            data=body,
            headers=self._base_headers(),
            timeout=30,
        ) as resp:
            response_data = await resp.json(content_type=None)

        if not isinstance(response_data, dict) or "data" not in response_data:
            _LOGGER.error("Unexpected Solax response shape for %s: %s", path, response_data)
            raise SolaxApiError(f"Unexpected Solax response: {response_data}")

        try:
            decrypted = self._decrypt(response_data["data"])
            parsed = json.loads(decrypted)
        except Exception as err:
            _LOGGER.exception("Failed to decrypt Solax response for %s", path)
            raise SolaxApiError(f"Failed to decrypt/parse response: {err}") from err

        _LOGGER.debug("Decrypted Solax response for %s: success=%s result=%s", path, parsed.get("success"), parsed.get("result"))

        return parsed

    async def async_unlock_with_pin(self) -> dict[str, Any] | None:
        if not self._pin:
            _LOGGER.debug("No PIN configured for inverter %s, skipping unlock", self._inverter_sn)
            return None

        _LOGGER.debug("Unlocking Solax settings for inverter %s using configured PIN", self._inverter_sn)

        payload = OrderedDict(
            [
                ("optType", "setReg"),
                ("sn", self._sn),
                ("inverterSn", self._inverter_sn),
                ("tokenId", self._token_id),
                ("num", 1),
                ("deviceType", 1),
                ("Data", '[{"reg":' + str(REG_PIN) + ',"val":"' + str(self._pin) + '"}]'),
            ]
        )
        return await self._post_encrypted("/app_api/settingnew/paramSet", payload)

    async def async_get_param_init(self) -> dict[str, Any]:
        _LOGGER.debug("Fetching paramInit for inverter %s", self._inverter_sn)
        payload = OrderedDict(
            [
                ("tokenId", self._token_id),
                ("sn", self._sn),
                ("inverterSn", self._inverter_sn),
                ("deviceType", 1),
            ]
        )
        return await self._post_encrypted("/app_api/settingnew/paramInit", payload)

    async def async_get_export_limit_w(self) -> int | None:
        await self.async_unlock_with_pin()
        data = await self.async_get_param_init()

        result = data.get("result")
        if not isinstance(result, list):
            _LOGGER.warning(
                "Unexpected paramInit result type for inverter %s: %s",
                self._inverter_sn,
                type(result).__name__,
            )
            return None

        # Common format: array where index == register number.
        if result and not isinstance(result[0], dict):
            if len(result) <= PARAMINIT_EXPORT_LIMIT_INDEX:
                _LOGGER.warning(
                    "paramInit result too short for index %s on inverter %s (len=%s)",
                    PARAMINIT_EXPORT_LIMIT_INDEX,
                    self._inverter_sn,
                    len(result),
                )
                return None

            try:
                reg_value = float(result[PARAMINIT_EXPORT_LIMIT_INDEX])
                export_limit = int(reg_value * 10)
                _LOGGER.debug(
                    "Current export limit for inverter %s is %s W (array index %s for register %s, value=%s)",
                    self._inverter_sn,
                    export_limit,
                    PARAMINIT_EXPORT_LIMIT_INDEX,
                    REG_EXPORT_LIMIT,
                    result[PARAMINIT_EXPORT_LIMIT_INDEX],
                )
                return export_limit
            except (TypeError, ValueError) as err:
                _LOGGER.warning(
                    "Invalid export limit array value at index %s for inverter %s: %s (%s)",
                    PARAMINIT_EXPORT_LIMIT_INDEX,
                    self._inverter_sn,
                    result[PARAMINIT_EXPORT_LIMIT_INDEX],
                    err,
                )
                return None

        # Alternative format: list of dicts with explicit reg/val pairs.
        for item in result:
            if isinstance(item, dict) and item.get("reg") == REG_EXPORT_LIMIT:
                val = item.get("val")
                try:
                    export_limit = int(float(val) * 10)
                    _LOGGER.debug("Current export limit for inverter %s is %s W", self._inverter_sn, export_limit)
                    return export_limit
                except (TypeError, ValueError):
                    _LOGGER.warning("Invalid export limit value from Solax for inverter %s: %s", self._inverter_sn, val)
                    return None

        _LOGGER.warning("Export limit register not found in paramInit result for inverter %s", self._inverter_sn)
        return None

    async def async_set_export_limit_w(self, watts: int) -> dict[str, Any]:
        reg_value = int(watts / 10)
        _LOGGER.info("Setting export limit for inverter %s to %s W (reg value %s)", self._inverter_sn, watts, reg_value)

        payload = OrderedDict(
            [
                ("optType", "setReg"),
                ("num", 1),
                ("sn", self._sn),
                ("inverterSn", self._inverter_sn),
                ("deviceType", 1),
                ("tokenId", self._token_id),
                ("Data", '[{"reg":' + str(REG_EXPORT_LIMIT) + ',"val":' + str(reg_value) + '}]'),
            ]
        )

        await self.async_unlock_with_pin()
        result = await self._post_encrypted("/app_api/settingnew/paramSet", payload)
        _LOGGER.info(
            "Set export limit response for inverter %s: success=%s result=%s",
            self._inverter_sn,
            result.get("success"),
            result.get("result"),
        )
        return result
