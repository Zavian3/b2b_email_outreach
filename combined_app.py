#!/usr/bin/env python3
"""
Combined Application Entry Point
Runs both automation engine and dashboard in one service
"""

import os
import sys
import threading
import subprocess
import time
import signal
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CombinedApp:
    def __init__(self):
        self.automation_process = None
        self.dashboard_process = None
        self.running = True
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self.stop_processes()
        sys.exit(0)
    
    def start_automation_engine(self):
        """Start the automation engine in background"""
        try:
            logger.info("🤖 Starting automation engine...")
            # Import and run automation directly to avoid subprocess overhead
            from peekr_automation_master import PeekrAutomationMaster
            
            # Use a flag to track successful initialization
            automation_success = threading.Event()
            automation_error = threading.Event()
            error_message = None
            
            def run_automation():
                try:
                    logger.info("🔧 Initializing automation engine...")
                    automation = PeekrAutomationMaster()
                    logger.info("✅ Automation engine initialized successfully")
                    automation_success.set()
                    automation.run_master_automation()
                except Exception as e:
                    nonlocal error_message
                    error_message = str(e)
                    logger.error(f"❌ Automation engine initialization failed: {e}")
                    automation_error.set()
            
            # Start automation in background thread
            automation_thread = threading.Thread(target=run_automation, daemon=True)
            automation_thread.start()
            
            # Wait for initialization to complete (max 30 seconds)
            if automation_success.wait(timeout=30):
                logger.info("✅ Automation engine started successfully")
                return True
            elif automation_error.is_set():
                logger.error(f"❌ Automation engine failed to start: {error_message}")
                return False
            else:
                logger.error("❌ Automation engine initialization timed out")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to start automation engine: {e}")
            return False
    
    def start_dashboard(self):
        """Start the Streamlit dashboard"""
        try:
            logger.info("📊 Starting admin dashboard...")
            
            # Get port from environment (Digital Ocean sets this)
            port = os.getenv('PORT', '8501')
            
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
            
            self.dashboard_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            logger.info(f"✅ Dashboard started on port {port}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start dashboard: {e}")
            return False
    
    def stop_processes(self):
        """Stop all running processes"""
        if self.dashboard_process:
            logger.info("🛑 Stopping dashboard...")
            self.dashboard_process.terminate()
            try:
                self.dashboard_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.dashboard_process.kill()
    
    def monitor_dashboard(self):
        """Monitor dashboard process and log output"""
        if not self.dashboard_process:
            return
        
        try:
            while self.running and self.dashboard_process.poll() is None:
                output = self.dashboard_process.stdout.readline()
                if output:
                    # Log dashboard output (remove newlines and streamlit noise)
                    line = output.strip()
                    if line and not any(noise in line.lower() for noise in ['collecting usage statistics', 'you can now view your streamlit app']):
                        logger.info(f"📊 Dashboard: {line}")
                time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error monitoring dashboard: {e}")
    
    def run(self):
        """Run the combined application"""
        logger.info("🚀 Starting Peekr B2B Automation (Combined Mode)")
        logger.info("=" * 50)
        
        # Start automation engine in background
        if not self.start_automation_engine():
            logger.error("❌ Failed to start automation engine")
            return 1
        
        # Give automation time to initialize
        time.sleep(5)
        
        # Start dashboard
        if not self.start_dashboard():
            logger.error("❌ Failed to start dashboard")
            return 1
        
        logger.info("✅ Both services started successfully!")
        logger.info("📊 Dashboard accessible via web interface")
        logger.info("🤖 Automation engine running in background")
        logger.info("🔄 Press Ctrl+C to stop all services")
        
        # Monitor dashboard output
        try:
            self.monitor_dashboard()
        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal")
        finally:
            self.stop_processes()
        
        return 0

def main():
    """Main entry point"""
    try:
        app = CombinedApp()
        return app.run()
    except Exception as e:
        logger.error(f"❌ Application failed to start: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())