#!/usr/bin/env python3
"""Test script to get device info from Solax API (read-only)."""

import asyncio
import aiohttp
import json
import sys
from typing import Any, Dict

# ============================================================================
# CONFIGURATION - Add your credentials here
# ============================================================================
SOLAX_CLIENT_ID = "your_client_id_here"
SOLAX_CLIENT_SECRET = "your_client_secret_here"
SOLAX_DEVICE_SN = "your_device_sn_here"  # Your device serial number
SOLAX_BASE_URL = "https://openapi-eu.solaxcloud.com"
# ============================================================================


async def get_access_token(
    client_id: str, client_secret: str, base_url: str = "https://openapi-eu.solaxcloud.com"
) -> str:
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


async def get_device_list(
    access_token: str,
    base_url: str = "https://openapi-eu.solaxcloud.com",
) -> Dict[str, Any]:
    """
    Get list of devices from Solax API.
    
    Args:
        access_token: OAuth access token
        base_url: API base URL (default EU)
    
    Returns:
        API response as dictionary
    """
    
    url = f"{base_url}/openapi/v2/device/list"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    
    print(f"\n🔗 URL: {url}")
    print(f"📤 Headers: {json.dumps({k: v if k != 'Authorization' else 'Bearer ***' for k, v in headers.items()}, indent=2)}")
    print("\n📡 Sending GET request...\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=30) as resp:
                response_data = await resp.json()
                
                print(f"✅ Status: {resp.status}")
                print(f"📥 Response: {json.dumps(response_data, indent=2)}")
                
                return response_data
        except Exception as err:
            print(f"❌ Error: {err}")
            raise


async def get_device_status(
    access_token: str,
    device_sn: str,
    base_url: str = "https://openapi-eu.solaxcloud.com",
) -> Dict[str, Any]:
    """
    Get device status from Solax API.
    
    Args:
        access_token: OAuth access token
        device_sn: Device serial number
        base_url: API base URL (default EU)
    
    Returns:
        API response as dictionary
    """
    
    url = f"{base_url}/openapi/v2/device/{device_sn}/realtime"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    
    print(f"\n🔗 URL: {url}")
    print(f"📤 Headers: {json.dumps({k: v if k != 'Authorization' else 'Bearer ***' for k, v in headers.items()}, indent=2)}")
    print("\n📡 Sending GET request...\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=30) as resp:
                response_data = await resp.json()
                
                print(f"✅ Status: {resp.status}")
                print(f"📥 Response: {json.dumps(response_data, indent=2)}")
                
                return response_data
        except Exception as err:
            print(f"❌ Error: {err}")
            raise


async def main():
    """Run the test with command line arguments or hardcoded config."""
    # Use hardcoded values if configured, otherwise fall back to command line args
    client_id = SOLAX_CLIENT_ID if SOLAX_CLIENT_ID != "your_client_id_here" else None
    client_secret = SOLAX_CLIENT_SECRET if SOLAX_CLIENT_SECRET != "your_client_secret_here" else None
    device_sn = SOLAX_DEVICE_SN if SOLAX_DEVICE_SN != "your_device_sn_here" else None
    base_url = SOLAX_BASE_URL
    
    # Fall back to command line arguments if not configured
    if not client_id or not client_secret:
        if len(sys.argv) < 3:
            print("Usage: python test_get_device_info.py <client_id> <client_secret> [device_sn] [base_url]")
            print("\nOR update the configuration at the top of this file:")
            print("  SOLAX_CLIENT_ID")
            print("  SOLAX_CLIENT_SECRET")
            print("  SOLAX_DEVICE_SN")
            print("\nExamples:")
            print("  # List all devices:")
            print("  python test_get_device_info.py your_client_id your_client_secret")
            print("\n  # Get status for specific device:")
            print("  python test_get_device_info.py your_client_id your_client_secret H34A10J3655008")
            print("\nParameters:")
            print("  client_id: Client ID from Solax Developer Portal")
            print("  client_secret: Client Secret from Solax Developer Portal")
            print("  device_sn: (Optional) Device serial number to get status")
            print("  base_url: (Optional) API base URL (default: https://openapi-eu.solaxcloud.com)")
            sys.exit(1)
        
        client_id = sys.argv[1]
        client_secret = sys.argv[2]
        device_sn = sys.argv[3] if len(sys.argv) > 3 else None
        base_url = sys.argv[4] if len(sys.argv) > 4 else "https://openapi-eu.solaxcloud.com"
    
    try:
        # Step 1: Get access token
        access_token = await get_access_token(client_id, client_secret, base_url)
        
        # Step 2: Get device list
        print("\n" + "="*60)
        print("📋 FETCHING DEVICE LIST")
        print("="*60)
        await get_device_list(access_token, base_url)
        
        # Step 3: Get device status if SN provided
        if device_sn:
            print("\n" + "="*60)
            print(f"📊 FETCHING DEVICE STATUS FOR {device_sn}")
            print("="*60)
            await get_device_status(access_token, device_sn, base_url)
        
        print("\n✅ All read-only tests completed successfully!")
        
    except Exception as err:
        print(f"\n❌ Test failed: {err}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
