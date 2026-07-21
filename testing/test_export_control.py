#!/usr/bin/env python3
"""Test Solax export control API via OAuth client credentials."""

import asyncio
import json
import sys
from typing import Any, Dict

import aiohttp

DEFAULT_BASE_URL = "https://openapi-eu.solaxcloud.com"


async def get_access_token(client_id: str, client_secret: str, base_url: str) -> str:
    """Get OAuth access token from the Solax open API."""
    url = f"{base_url}/openapi/auth/oauth/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }

    print(f"\nGetting access token from: {url}")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        ) as resp:
            try:
                response_data = await resp.json()
            except Exception:
                response_data = {"raw": await resp.text()}

            if resp.status == 200 and response_data.get("code") == 0:
                token = response_data["result"]["access_token"]
                expires = response_data["result"].get("expires_in")
                print(f"Token received (expires in {expires} seconds)")
                return token

            raise RuntimeError(f"Token request failed: HTTP {resp.status} {response_data}")


async def set_export_control(
    access_token: str,
    device_sn: str,
    limit_value_kw: float,
    is_enable: int,
    base_url: str,
    device_type: int = 100,
    control_mode: int = 1,
    business_type: int = 4,
) -> Dict[str, Any]:
    """Call the export-control endpoint."""
    url = f"{base_url}/openapi/v2/device/device_control/strategy/set_export_control"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    payload = {
        "snList": [device_sn],
        "deviceType": device_type,
        "isEnable": is_enable,
        "controlMode": control_mode,
        "limitValue": limit_value_kw,
        "businessType": business_type,
    }

    print(f"\nCalling export-control endpoint: {url}")
    print(
        "Request headers: "
        + json.dumps(
            {
                k: (v if k != "Authorization" else "Bearer ***")
                for k, v in headers.items()
            },
            indent=2,
        )
    )
    print("Request payload: " + json.dumps(payload, indent=2))

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers, timeout=30) as resp:
            try:
                response_data = await resp.json()
            except Exception:
                response_data = {"raw": await resp.text()}

            print(f"Response status: {resp.status}")
            print("Response body: " + json.dumps(response_data, indent=2))
            return response_data


async def main() -> None:
    if len(sys.argv) < 4:
        print(
            "Usage: python3 test_export_control.py <client_id> <client_secret> <device_sn> "
            "[limit_value_kw] [is_enable] [base_url]"
        )
        print("Example: python3 test_export_control.py cid csecret H34A10J3655008 1.0 1")
        sys.exit(1)

    client_id = sys.argv[1]
    client_secret = sys.argv[2]
    device_sn = sys.argv[3]
    limit_value_kw = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    is_enable = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    base_url = sys.argv[6] if len(sys.argv) > 6 else DEFAULT_BASE_URL

    token = await get_access_token(client_id, client_secret, base_url)
    await set_export_control(
        access_token=token,
        device_sn=device_sn,
        limit_value_kw=limit_value_kw,
        is_enable=is_enable,
        base_url=base_url,
    )


if __name__ == "__main__":
    asyncio.run(main())
