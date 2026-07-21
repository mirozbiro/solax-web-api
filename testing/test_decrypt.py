#!/usr/bin/env python3
"""Test decryption of captured Solax encrypted payload."""

import base64
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import hashlib

# ============================================================================
# CONFIGURATION - Update with your actual credentials
# ============================================================================
PIN = "your_pin_here"
USERNAME = "your_username_here"
DEVICE_SN = "your_inverter_sn_here"
TOKEN_ID = "your_token_id_here"  # From localStorage/sessionStorage
WIFI_SN = "your_wifi_sn_here"

# Captured encrypted request payload (URL decoded)
REQUEST_ENCRYPTED = "tpLbCxIMfz+iOeybk4egc650GuOHxeiSkmTOSxQUZPuad3653CpE/5MlWuu5WbV2S47Di2vHvjWSQqHRF2LCepst11rxLJjIvR7QrWIpcFT9M9ZDNCfH3fz3NeM42jWwXMHU4yF6fV7QU3QOcZD0K2oXl2aO8mEpCI6TG9uQ9ArQuJkA4zAlDcPv62p73u6AHgF+KKnLtXaST/Xw992kAeAChadkOG6YzHfhGU/KDFw="

# Response payload
RESPONSE_ENCRYPTED = "w0Xvn9+G7FPnOa/mBMZvgUX1KlzXKIsVDll7BJuay0I9c5seofiBV2SeR7Hz0qoV6ppa39DEliWP82irWwgeKX2YixP7/aT8Kx6L61x5dmXxN3LOzwq9Qoh+H0oCH7SqvQ+pJSV4qOxmHZQTvJxWpAHhMwqJNxgHgf01ETNvIJE="

# Control data: changed from 0 to 1000W export control
CONTROL_INFO = "Device SN: your_inverter_sn_here, Export Control: 0 -> 1000W"

CRYPTO_VER = 1  # From the header: crytoVer: 1
# ============================================================================


def try_aes_decrypt(encrypted_b64: str, key: bytes, iv_bytes: bytes = None) -> dict:
    """
    Try to decrypt AES-CBC encrypted data.
    
    Args:
        encrypted_b64: Base64 encoded encrypted data
        key: Encryption key (bytes, should be 16, 24, or 32 bytes for AES)
        iv_bytes: IV (16 bytes), if None extracted from first 16 bytes of ciphertext
    
    Returns:
        dict with status and decrypted content
    """
    try:
        encrypted_data = base64.b64decode(encrypted_b64)
        
        if iv_bytes is None:
            # Pattern 1: IV prepended to ciphertext
            iv = encrypted_data[:16]
            ciphertext = encrypted_data[16:]
        else:
            iv = iv_bytes
            ciphertext = encrypted_data
        
        # Try different key sizes (AES supports 16, 24, 32 bytes)
        actual_key = key
        if len(key) > 32:
            actual_key = key[:32]
        
        cipher = AES.new(actual_key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(ciphertext)
        
        # Try to unpad
        try:
            decrypted = unpad(decrypted, AES.block_size)
        except:
            pass
        
        try:
            text = decrypted.decode('utf-8')
            return {"success": True, "text": text, "hex": decrypted.hex()}
        except:
            return {"success": False, "hex": decrypted.hex(), "raw": decrypted}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    print("="*80)
    print("🔐 SOLAX ENCRYPTION ANALYSIS - cryptoVer: 1")
    print("="*80)
    print(f"\nControl Info: {CONTROL_INFO}")
    print(f"Encrypted Request (base64):\n  {REQUEST_ENCRYPTED}\n")
    print(f"Encrypted Response (base64):\n  {RESPONSE_ENCRYPTED}\n")
    
    # Possible keys to try
    key_candidates = [
        ("TokenId as hex (direct)", bytes.fromhex(TOKEN_ID)),
        ("TokenId as SHA256", hashlib.sha256(TOKEN_ID.encode()).digest()),
        ("WiFi SN as SHA256", hashlib.sha256(WIFI_SN.encode()).digest()),
        ("Device SN as SHA256", hashlib.sha256(DEVICE_SN.encode()).digest()),
        ("TokenId + WiFi SN", hashlib.sha256((TOKEN_ID + WIFI_SN).encode()).digest()),
        ("TokenId + Device SN", hashlib.sha256((TOKEN_ID + DEVICE_SN).encode()).digest()),
        ("PIN as SHA256", hashlib.sha256(PIN.encode()).digest()),
        ("Username as SHA256", hashlib.sha256(USERNAME.encode()).digest()),
        ("PIN+Username as SHA256", hashlib.sha256((PIN + USERNAME).encode()).digest()),
        ("PIN as MD5 padded", hashlib.md5(PIN.encode()).digest() + b'\x00' * 16),
    ]
    
    print("\n" + "="*80)
    print("ATTEMPTING DECRYPTION WITH VARIOUS KEYS")
    print("="*80)
    
    for key_name, key_bytes in key_candidates:
        print(f"\n[{key_name}]")
        print(f"  Key (hex): {key_bytes.hex()}")
        print(f"  Key length: {len(key_bytes)} bytes")
        
        result = try_aes_decrypt(REQUEST_ENCRYPTED, key_bytes)
        
        if result["success"]:
            print(f"  ✅ DECRYPTION SUCCESSFUL!")
            print(f"  Decrypted text:\n    {result['text']}")
            print(f"\n🎉 FOUND IT! Use this key for encryption:")
            print(f"   Key: {key_bytes.hex()}")
            print(f"   Method: {key_name}")
            return
        else:
            print(f"  ❌ Failed: {result.get('error', 'No error')}")
            if "hex" in result and result.get("hex"):
                print(f"  Raw hex (first 32 bytes): {result['hex'][:64]}")
    
    print("\n" + "="*80)
    print("\n⚠️  None of the keys worked. We need more information:")
    print("\n1. Check if there's a STATIC key/IV in the JavaScript code")
    print("2. Check browser cookies/localStorage for any encryption keys")
    print("3. Verify if PIN format is correct (numeric string, or something else?)")
    print("4. Check if encryption uses IV from response or a constant IV")
    print("\nTo debug further:")
    print("  - Use browser DevTools to intercept the encryption function")
    print("  - Add console.log() to capture the key/IV before encryption")
    print("  - Or find the JavaScript encryption library and analyze its parameters")


if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("Error: pycryptodome not installed")
        print("Install with: pipx install pycryptodome")
