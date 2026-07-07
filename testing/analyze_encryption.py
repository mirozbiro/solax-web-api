#!/usr/bin/env python3
"""Recreate the Solax web-app encryption for the export-control request."""

import base64
from collections import OrderedDict
from urllib.parse import quote
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# From the browser bundle:
KEY = "hj7x22H$yuBI0456"
IV = "NIfb&74GUY86Gfgh"

# Example payload captured from the browser
CAPTURED_REQUEST = "tpLbCxIMfz+iOeybk4egc650GuOHxeiSkmTOSxQUZPuad3653CpE/5MlWuu5WbV2S47Di2vHvjWSQqHRF2LCepst11rxLJjIvR7QrWIpcFT9M9ZDNCfH3fz3NeM42jWwXMHU4yF6fV7QU3QOcZD0K2oXl2aO8mEpCI6TG9uQ9ArQuJkA4zAlDcPv62p73u6AHgF+KKnLtXaST/Xw992kAeAChadkOG6YzHfhGU/KDFw="


def serialize_params(params: OrderedDict) -> str:
    """Mirror the JS helper: encodeURIComponent(key)=encodeURIComponent(value)."""
    parts = []
    for key, value in params.items():
        if value is None:
            parts.append(f"{quote(str(key), safe='')}=")
        else:
            parts.append(f"{quote(str(key), safe='')}={quote(str(value), safe='')}")
    return "&".join(parts)


def encrypt_payload(params: OrderedDict) -> str:
    """Encrypt the params exactly as the Solax web app does."""
    plaintext = serialize_params(params).encode("utf-8")
    padded = pad(plaintext, AES.block_size)
    cipher = AES.new(KEY.encode("utf-8"), AES.MODE_CBC, IV.encode("utf-8"))
    ciphertext = cipher.encrypt(padded)
    return base64.b64encode(ciphertext).decode("ascii")


def decrypt_payload(payload_b64: str) -> str:
    """Decrypt the payload using the same fixed key and IV."""
    raw = base64.b64decode(payload_b64)
    cipher = AES.new(KEY.encode("utf-8"), AES.MODE_CBC, IV.encode("utf-8"))
    padded_plain = cipher.decrypt(raw)
    return unpad(padded_plain, AES.block_size).decode("utf-8")


def main() -> None:
    params = OrderedDict([
        ("optType", "setReg"),
        ("num", 1),
        ("sn", "SYAAD8TBMH"),
        ("inverterSn", "H34A10J3655008"),
        ("deviceType", 1),
        ("tokenId", "68881b0be2a9ad4c51c4f5da1b46875b"),
        ("Data", '[{"reg":48,"val":100}]'),
    ])

    print("Plaintext (URL-encoded):")
    print(serialize_params(params))
    print()
    print("Encrypted body data:")
    print(encrypt_payload(params))
    print()
    print("Encrypted query parameter value:")
    print(quote(encrypt_payload(params), safe=""))
    print()
    print("Decrypted captured payload:")
    print(decrypt_payload(CAPTURED_REQUEST))


if __name__ == "__main__":
    main()
