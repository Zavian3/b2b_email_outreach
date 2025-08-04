#!/usr/bin/env python3
"""
Encode Google Credentials for Digital Ocean Environment Variables
This script converts your credentials.json to a base64 string for secure deployment
"""

import json
import base64
import os

def encode_credentials_file(file_path):
    """Encode credentials file to base64 string"""
    try:
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return None
        
        with open(file_path, 'r') as f:
            credentials_data = json.load(f)
        
        # Convert to JSON string then to base64
        json_string = json.dumps(credentials_data)
        encoded_string = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')
        
        print(f"✅ Successfully encoded {file_path}")
        print("\n🔐 Base64 Encoded Credentials:")
        print("=" * 50)
        print(encoded_string)
        print("=" * 50)
        print("\n📋 Instructions:")
        print("1. Copy the base64 string above")
        print("2. In Digital Ocean App Platform:")
        print("   - Go to your app settings")
        print("   - Navigate to Environment Variables")
        print("   - Add new variable:")
        print("     Key: GOOGLE_CREDENTIALS_JSON")
        print("     Value: [paste the base64 string]")
        print("     Type: Secret")
        print("3. Deploy your app")
        
        return encoded_string
        
    except Exception as e:
        print(f"❌ Error encoding credentials: {e}")
        return None

def main():
    print("🔧 Google Credentials Encoder for Digital Ocean")
    print("=" * 50)
    
    # Look for credentials file
    possible_files = [
        'peekr-465815-94dae74a243d.json',
        'credentials.json',
        'service-account.json',
        'google-credentials.json'
    ]
    
    credentials_file = None
    for file_path in possible_files:
        if os.path.exists(file_path):
            credentials_file = file_path
            break
    
    if not credentials_file:
        print("❌ No credentials file found!")
        print("\nLooking for one of these files:")
        for f in possible_files:
            print(f"  - {f}")
        print("\nPlease ensure your Google Service Account credentials file is in this directory.")
        return
    
    print(f"📁 Found credentials file: {credentials_file}")
    encoded = encode_credentials_file(credentials_file)
    
    if encoded:
        # Save to file for backup
        with open('encoded_credentials.txt', 'w') as f:
            f.write(encoded)
        print(f"\n💾 Encoded string also saved to: encoded_credentials.txt")

if __name__ == "__main__":
    main()