#!/usr/bin/env python3
"""Download and analyze Solax web app JavaScript files for encryption logic."""

import asyncio
import aiohttp
import sys
import re
from typing import List

# Base URL of the Solax web application
SOLAX_APP_URL = "https://euapp.solaxcloud.com"

# Common keywords that indicate encryption
ENCRYPTION_KEYWORDS = [
    "encrypt", "decrypt", "AES", "RSA", "crypto", "cipher",
    "CryptoJS", "aes", "hash", "sha256", "md5", "hmac",
    "publicKey", "privateKey", "encode", "decode"
]


async def download_file(url: str) -> str:
    """Download a file from URL."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as resp:
                if resp.status == 200:
                    return await resp.text()
    except Exception as e:
        print(f"❌ Failed to download {url}: {e}")
    return None


async def search_for_encryption(content: str, filename: str) -> List[str]:
    """Search content for encryption-related code."""
    results = []
    
    for keyword in ENCRYPTION_KEYWORDS:
        pattern = re.compile(keyword, re.IGNORECASE)
        matches = pattern.findall(content)
        
        if matches:
            results.append(f"Found '{keyword}': {len(matches)} occurrences")
    
    return results


async def main():
    if len(sys.argv) < 2:
        print("Usage: python find_encryption.py <solax_app_url> [search_term]")
        print("\nExample:")
        print("  python find_encryption.py https://euapp.solaxcloud.com")
        print("  python find_encryption.py https://euapp.solaxcloud.com crypto")
        print("\nThis script will:")
        print("1. Attempt to find JavaScript files")
        print("2. Search them for encryption-related keywords")
        print("3. Extract and display encryption functions")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    search_term = sys.argv[2].lower() if len(sys.argv) > 2 else None
    
    print("="*70)
    print("🔍 SOLAX JAVASCRIPT ENCRYPTION ANALYSIS")
    print("="*70)
    
    # Common chunk patterns based on the HTML you provided
    js_files = [
        "js/chunk-d939e436.4f536e1d.js",
        "js/chunk-308efcfa.e0ae26cc.js",
        "js/chunk-1d3a2b00.b7a3860a.js",
        "js/chunk-10080b82.c29ed194.js",
        "js/chunk-298c8dd6.a0cdc43b.js",
        "js/chunk-065089ee.0fbfa8c2.js",
        "js/chunk-2d0bb1fc.5955c4b6.js",
        "js/chunk-f50a39ea.1c143cca.js",
        "js/app.js",
        "js/main.js",
    ]
    
    print(f"\nBase URL: {base_url}")
    print(f"Searching for encryption keywords in JavaScript files...\n")
    
    for js_file in js_files:
        url = f"{base_url}/{js_file}"
        print(f"📥 Downloading: {url}")
        
        content = await download_file(url)
        
        if content:
            results = await search_for_encryption(content, js_file)
            
            if results:
                print(f"✅ Found in {js_file}:")
                for result in results:
                    print(f"   - {result}")
                
                # Try to extract encryption function
                if "encrypt" in content.lower() or "aes" in content.lower():
                    print(f"\n   💡 This file likely contains encryption logic!")
                    print(f"   Save it for manual analysis:")
                    print(f"      curl -o solax_{js_file.split('/')[-1]} {url}")
            else:
                print(f"   ℹ️ No encryption keywords found")
        else:
            print(f"   ❌ Could not download")
        
        print()
    
    print("="*70)
    print("\n📋 Next steps:")
    print("1. If you found a promising file above, download it:")
    print("   curl -o solax_encrypted.js https://euapp.solaxcloud.com/js/chunk-XXXXX.js")
    print("\n2. Open it in a text editor and search for 'encrypt' or 'AES'")
    print("\n3. Look for patterns like:")
    print("   - CryptoJS.AES.encrypt(data, key)")
    print("   - crypto.encrypt(data, passphrase)")
    print("   - var key = ... var iv = ...")
    print("\n4. Share the encryption function with me")


if __name__ == "__main__":
    asyncio.run(main())
