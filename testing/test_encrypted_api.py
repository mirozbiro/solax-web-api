#!/usr/bin/env python3
"""Test script for Solax web API export control (encrypted payload)."""

import asyncio
import base64
import json
import time
import uuid
from collections import OrderedDict
from typing import Any, Dict
from urllib.parse import quote

import aiohttp
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# ============================================================================
# CONFIGURATION - Add your credentials here
# ============================================================================
SOLAX_DEVICE_SN = "your_inverter_sn_here"
SOLAX_TOKEN_ID = "your_token_id_here"
SOLAX_SN = "your_wifi_sn_here"

# Fixed values discovered from the browser bundle
AES_KEY = "hj7x22H$yuBI0456"
AES_IV = "NIfb&74GUY86Gfgh"

# Easy-to-edit export limit setting (watts)
# The browser maps this to Data value as watts / 10.
EXPORT_LIMIT_WATTS = 9500
EXPORT_LIMIT_REG_VALUE = int(EXPORT_LIMIT_WATTS / 10)
EXPORT_LIMIT_DATA = f'[{{"reg":48,"val":{EXPORT_LIMIT_REG_VALUE}}}]'

# Easy-to-edit write mode
# - "export": write export limit via reg 48 (value = watts/10)
# - "pin": write installer PIN via reg 0 (value must be a string)
WRITE_MODE = "export"
PIN_VALUE = "your_pin_here"
# ============================================================================


def serialize_params(params: OrderedDict) -> str:
    parts = []
    for key, value in params.items():
        parts.append(f"{quote(str(key), safe='')}={quote(str(value), safe='')}")
    return "&".join(parts)


def encrypt_payload(params: OrderedDict) -> str:
    plaintext = serialize_params(params).encode("utf-8")
    padded = pad(plaintext, AES.block_size)
    cipher = AES.new(AES_KEY.encode("utf-8"), AES.MODE_CBC, AES_IV.encode("utf-8"))
    return base64.b64encode(cipher.encrypt(padded)).decode("ascii")


def build_query_payload() -> str:
    params = OrderedDict([
        ("timeStamp", int(time.time() * 1000)),
        ("requestId", uuid.uuid4().hex),
    ])
    return encrypt_payload(params)


def decrypt_payload(payload_b64: str) -> str:
    raw = base64.b64decode(payload_b64)
    cipher = AES.new(AES_KEY.encode("utf-8"), AES.MODE_CBC, AES_IV.encode("utf-8"))
    padded = cipher.decrypt(raw)
    return unpad(padded, AES.block_size).decode("utf-8")


async def test_web_api_endpoint(body_payload: str, query_payload: str) -> Dict[str, Any]:
    url = "https://euapi.solaxcloud.com/app_api/settingnew/paramSet"
    query_data = quote(query_payload, safe="")
    full_url = f"{url}?data={query_data}"

    headers = {
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

    body = {"data": body_payload}

    print(f"\n🔗 URL: {full_url}")
    print(f"📤 Headers: {json.dumps(headers, indent=2)}")
    print(f"📋 Body: {json.dumps(body, indent=2)}")
    print(f"📋 Query payload: {query_payload}")
    print("\n📡 Sending POST request...\n")

    async with aiohttp.ClientSession() as session:
        async with session.post(full_url, data=body, headers=headers, timeout=30) as resp:
            try:
                response_data = await resp.json()
            except Exception:
                response_data = await resp.text()

            print(f"✅ Status: {resp.status}")
            print(f"📥 Response: {json.dumps(response_data, indent=2) if isinstance(response_data, dict) else response_data}")
            if isinstance(response_data, dict) and response_data.get("data"):
                print("\n🧩 Decrypted response:")
                print(decrypt_payload(response_data["data"]))
            return response_data


async def main() -> None:
    print("=" * 60)
    print("🔐 SOLAX WEB API TEST (ENCRYPTED PAYLOAD)")
    print("=" * 60)

    if WRITE_MODE == "pin":
        data_field = '[{"reg":0,"val":"' + PIN_VALUE + '"}]'
    else:
        data_field = EXPORT_LIMIT_DATA

    params = OrderedDict([
        ("optType", "setReg"),
        ("num", 1),
        ("sn", SOLAX_SN),
        ("inverterSn", SOLAX_DEVICE_SN),
        ("deviceType", 1),
        ("tokenId", SOLAX_TOKEN_ID),
        ("Data", data_field),
    ])

    body_payload = encrypt_payload(params)
    query_payload = build_query_payload()
    print("\nEncrypted body payload:")
    print(body_payload)
    print("\nEncrypted query payload:")
    print(query_payload)

    await test_web_api_endpoint(body_payload, query_payload)


if __name__ == "__main__":
    asyncio.run(main())
