#!/usr/bin/env python3
"""
Email Fetching Diagnostic Script
Helps diagnose email fetching issues on the server
"""

import os
import sys
import imaplib
import socket
from datetime import datetime
from config import Config

def test_dns_resolution():
    """Test DNS resolution for IMAP server"""
    print("🔍 Testing DNS resolution...")
    try:
        imap_server = Config.IMAP_SERVER
        ip = socket.gethostbyname(imap_server)
        print(f"✅ DNS resolution successful: {imap_server} -> {ip}")
        return True
    except Exception as e:
        print(f"❌ DNS resolution failed: {e}")
        return False

def test_imap_connection():
    """Test IMAP connection"""
    print("🔍 Testing IMAP connection...")
    try:
        mail = imaplib.IMAP4_SSL(Config.IMAP_SERVER, Config.IMAP_PORT)
        print(f"✅ IMAP connection successful to {Config.IMAP_SERVER}:{Config.IMAP_PORT}")
        
        # Test login
        mail.login(Config.EMAIL_ACCOUNT, Config.EMAIL_PASSWORD)
        print(f"✅ IMAP login successful for {Config.EMAIL_ACCOUNT}")
        
        # Test inbox selection
        mail.select("inbox")
        print("✅ Inbox selection successful")
        
        # Check for emails
        result, data = mail.search(None, "ALL")
        if result == 'OK':
            email_ids = data[0].split()
            print(f"✅ Found {len(email_ids)} emails in inbox")
        else:
            print("⚠️ Could not search emails")
        
        mail.close()
        mail.logout()
        return True
        
    except Exception as e:
        print(f"❌ IMAP connection/login failed: {e}")
        return False

def test_environment_variables():
    """Test if all required environment variables are set"""
    print("🔍 Testing environment variables...")
    required_vars = [
        'EMAIL_ACCOUNT', 'EMAIL_PASSWORD', 'IMAP_SERVER', 'IMAP_PORT',
        'SMTP_SERVER', 'SMTP_PORT', 'OPENAI_API_KEY', 'SPREADSHEET_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = getattr(Config, var, None)
        if not value:
            missing_vars.append(var)
        else:
            # Don't print sensitive values
            if 'PASSWORD' in var or 'KEY' in var:
                print(f"✅ {var}: [SET]")
            else:
                print(f"✅ {var}: {value}")
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def test_google_sheets_connection():
    """Test Google Sheets connection"""
    print("🔍 Testing Google Sheets connection...")
    try:
        from credentials_helper import get_google_sheets_client
        gc = get_google_sheets_client()
        
        # Try to open the spreadsheet
        sheet = gc.open_by_key(Config.SPREADSHEET_ID)
        print(f"✅ Google Sheets connection successful: {sheet.title}")
        
        # Try to access worksheets
        try:
            incoming_leads = sheet.worksheet("Incoming Leads")
            print("✅ 'Incoming Leads' worksheet accessible")
        except:
            print("⚠️ 'Incoming Leads' worksheet not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Google Sheets connection failed: {e}")
        return False

def main():
    """Run all diagnostic tests"""
    print("🚀 PEEKR EMAIL FETCHING DIAGNOSTIC")
    print("=" * 50)
    print(f"⏰ Test time: {datetime.now()}")
    print(f"🌍 Timezone: {Config.TIMEZONE}")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("DNS Resolution", test_dns_resolution),
        ("IMAP Connection", test_imap_connection),
        ("Google Sheets", test_google_sheets_connection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        print("-" * 30)
        if test_func():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 DIAGNOSTIC SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Email fetching should work.")
        print("💡 If emails are still not being fetched, check:")
        print("   - Is the automation engine actually running?")
        print("   - Check the logs in peekr_automation.log")
        print("   - Verify the server is using combined_app.py, not simple_dashboard.py")
    else:
        print("❌ Some tests failed. Fix the issues above.")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
