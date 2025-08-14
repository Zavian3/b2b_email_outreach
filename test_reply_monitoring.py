#!/usr/bin/env python3
"""
Quick test to demonstrate reply monitoring functionality
"""

import sys
import threading
import time
from peekr_automation_master import PeekrAutomationMaster

def test_reply_monitoring():
    """Test the reply monitoring system briefly"""
    print("🧪 TESTING REPLY MONITORING SYSTEM")
    print("=" * 50)
    
    try:
        # Initialize automation
        automation = PeekrAutomationMaster()
        print("✅ Automation system initialized")
        
        # Start reply monitoring in background
        def start_monitoring():
            try:
                automation.start_realtime_reply_monitoring()
                print("✅ Reply monitoring started successfully")
            except Exception as e:
                print(f"❌ Reply monitoring failed: {e}")
        
        monitor_thread = threading.Thread(target=start_monitoring, daemon=True)
        monitor_thread.start()
        
        print("⏳ Testing for 30 seconds...")
        print("💡 Check the status with: python3 check_automation_status.py")
        print("🛑 Press Ctrl+C to stop the test")
        
        # Run for 30 seconds
        time.sleep(30)
        
        print("✅ Test completed")
        
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    print("👋 Test finished")

if __name__ == "__main__":
    test_reply_monitoring()
