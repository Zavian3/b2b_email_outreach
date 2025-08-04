#!/usr/bin/env python3
"""
Google Credentials Helper for Digital Ocean Deployment
This script helps handle Google Service Account credentials securely
"""

import os
import json
import base64
import gspread
from google.oauth2.service_account import Credentials
from config import Config

def create_credentials_from_env():
    """Create credentials from environment variable (base64 encoded JSON)"""
    try:
        # ONLY use environment variable - no file fallback
        if Config.GOOGLE_CREDENTIALS_JSON:
            # Decode base64 JSON
            credentials_json = base64.b64decode(Config.GOOGLE_CREDENTIALS_JSON).decode('utf-8')
            credentials_data = json.loads(credentials_json)
            
            # Create temporary credentials file
            temp_cred_file = '/tmp/credentials.json'
            with open(temp_cred_file, 'w') as f:
                json.dump(credentials_data, f)
            
            return temp_cred_file
        
        else:
            raise FileNotFoundError("GOOGLE_CREDENTIALS_JSON environment variable not found")
            
    except Exception as e:
        print(f"ERROR: Failed to create credentials: {e}")
        return None

def get_google_sheets_client():
    """Get authenticated Google Sheets client"""
    try:
        credentials_file = create_credentials_from_env()
        if not credentials_file:
            raise Exception("No credentials file available")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(credentials_file, scopes=scope)
        client = gspread.authorize(creds)
        
        return client
        
    except Exception as e:
        print(f"ERROR: Failed to create Google Sheets client: {e}")
        return None

def test_credentials():
    """Test Google Sheets connectivity"""
    try:
        client = get_google_sheets_client()
        if client:
            # Try to open the spreadsheet
            sheet = client.open_by_key(Config.SPREADSHEET_ID)
            print(f"✅ Successfully connected to Google Sheets: {sheet.title}")
            return True
        else:
            print("❌ Failed to create Google Sheets client")
            return False
            
    except Exception as e:
        print(f"❌ Google Sheets test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Google Sheets credentials...")
    test_credentials()