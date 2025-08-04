#!/usr/bin/env python3
"""
Simple Dashboard for Testing Digital Ocean Deployment
"""

import os
import subprocess
import sys

def main():
    """Run just the Streamlit dashboard for testing"""
    print("🚀 Starting Peekr Dashboard (Simple Mode)")
    print("=" * 50)
    
    # Get port from environment (Digital Ocean sets this)
    port = os.getenv('PORT', '8501')
    print(f"📊 Starting dashboard on port {port}")
    
    # Start Streamlit dashboard
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 
        'admin_dashboard.py',
        '--server.port', str(port),
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--server.enableCORS', 'false',
        '--server.enableXsrfProtection', 'false'
    ]
    
    print(f"🔧 Running command: {' '.join(cmd)}")
    
    # Run directly (not as subprocess for simpler debugging)
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())