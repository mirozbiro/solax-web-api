#!/usr/bin/env python3
"""Test decryption of captured Solax encrypted payload."""

import base64
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import hashlib

# ============================================================================
# CONFIGURATION
# ============================================================================
PIN = "your_pin_here"
USERNAME = "your_username_here"
DEVICE_SN = "H34A10J3655008"

# Captured encrypted request payload (URL decoded)
REQUEST_ENCRYPTED = "tpLbCxIMfz+iOeybk4egc650GuOHxeiSkmTOSxQUZPuad3653CpE/5MlWuu5WbV2S47Di2vHvjWSQqHRF2LCepst11rxLJjIvR7QrWIpcFT9M9ZDNCfH3fz3NeM42jWwXMHU4yF6fV7QU3QOcZD0K2oXl2aO8mEpCI6TG9uQ9ArQuJkA4zAlDcPv62p73u6AHgF+KKnLtXaST/Xw992kAeAChadkOG6YzHfhGU/KDFw="

# Response payload
RESPONSE_ENCRYPTED = "w0Xvn9+G7FPnOa/mBMZvgUX1KlzXKIsVDll7BJuay0I9c5seofiBV2SeR7Hz0qoV6ppa39DEliWP82irWwgeKX2YixP7/aT8Kx6L61x5dmXxN3LOzwq9Qoh+H0oCH7SqvQ+pJSV4qOxmHZQTvJxWpAHhMwqJNxgHgf01ETNvIJE="

# Control data: changed from 0 to 1000W export control
CONTROL_INFO = "Device SN: H34A10J3655008, Export Control: 0 -> 1000W"

CRYPTO_VER = 1  # From the header: crytoVer: 1
# ============================================================================


def try_aes_decrypt(encrypted_b64: str, key: bytes, iv_bytes: bytes = None) -> dict:
    """
    Get access token from Solax OAuth endpoint.
    
    Args:
        client_id: Client ID from Solax Developer Portal
        client_secret: Client Secret from Solax Developer Portal
        base_url: API base URL (default EU)
    
    Returns:
        Access token string
    """
    
    url = f"{base_url}/openapi/auth/oauth/token"
    
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    
    print(f"\n🔐 Getting access token from: {url}")
    print(f"📤 Client ID: {client_id[:10]}...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
            ) as resp:
                response_data = await resp.json()
                
                if resp.status == 200 and response_data.get("code") == 0:
                    access_token = response_data["result"]["access_token"]
                    expires_in = response_data["result"]["expires_in"]
                    print(f"✅ Token obtained successfully (expires in {expires_in} seconds)")
                    return access_token
                else:
                    print(f"❌ Token request failed: {response_data}")
                    raise Exception(f"Failed to get access token: {response_data}")
        except Exception as err:
            print(f"❌ Error getting token: {err}")
            raise


async def test_export_control(
    access_token: str,
    device_sn: str,
    limit_value: float = 1.0,
    is_enable: int = 1,
    device_type: int = 100,
    control_mode: int = 1,
    business_type: int = 4,
    base_url: str = "https://openapi-eu.solaxcloud.com",
) -> Dict[str, Any]:
    """
    Test the export control endpoint.
    
    Args:
        access_token: OAuth access token
        device_sn: Device serial number
        limit_value: Export limit in kW (default 1.0)
        is_enable: 0 to disable, 1 to enable (default 1)
        device_type: Device type (default 100)
        control_mode: Control mode (default 1 for overall control)
        business_type: 1 for residential, 4 for commercial (default 4)
        base_url: API base URL (default EU)
    
    Returns:
        API response as dictionary
    """
    
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
        "limitValue": limit_value,
        "businessType": business_type,
    }
    
    print(f"\n🔗 URL: {url}")
    print(f"📤 Headers: {json.dumps({k: v if k != 'Authorization' else 'Bearer ***' for k, v in headers.items()}, indent=2)}")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    print("\n📡 Sending request...\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, headers=headers, timeout=30) as resp:
                response_data = await resp.json()
                
                print(f"✅ Status: {resp.status}")
                print(f"📥 Response: {json.dumps(response_data, indent=2)}")
                
                return response_data
        except Exception as err:
            print(f"❌ Error: {err}")
            raise


async def main():
    """Run the test with command line arguments."""
    if len(sys.argv) < 4:
        print("Usage: python test_export_control.py <client_id> <client_secret> <device_sn> [limit_value] [is_enable] [base_url]")
        print("\nExample:")
        print("  python test_export_control.py your_client_id your_client_secret H34A10J3655008 1.5 1")
        print("\nParameters:")
        print("  client_id: Client ID from Solax Developer Portal")
        print("  client_secret: Client Secret from Solax Developer Portal")
        print("  device_sn: Device serial number (e.g., H34A10J3655008)")
        print("  limit_value: Export limit in kW (default: 1.0)")
        print("  is_enable: 1 to enable, 0 to disable (default: 1)")
        print("  base_url: API base URL (default: https://openapi-eu.solaxcloud.com)")
        sys.exit(1)
    
    client_id = sys.argv[1]
    client_secret = sys.argv[2]
    device_sn = sys.argv[3]
    limit_value = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    is_enable = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    base_url = sys.argv[6] if len(sys.argv) > 6 else "https://openapi-eu.solaxcloud.com"
    
    try:
        # Step 1: Get access token
        access_token = await get_access_token(client_id, client_secret, base_url)
        
        # Step 2: Test export control
        await test_export_control(
            access_token=access_token,
            device_sn=device_sn,
            limit_value=limit_value,
            is_enable=is_enable,
            base_url=base_url,
        )
    except Exception as err:
        print(f"\n❌ Test failed: {err}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
