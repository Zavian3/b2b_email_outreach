#!/usr/bin/env python3
"""
Automation Status Checker
Shows real-time status of the Peekr automation engine
"""

import os
import sys
import psutil
import pytz
from datetime import datetime, timedelta
from config import Config
import logging
import json

def get_server_time_info():
    """Get comprehensive time information"""
    print("🕐 SERVER TIME INFORMATION")
    print("=" * 50)
    
    # Current UTC time
    utc_now = datetime.now(pytz.UTC)
    print(f"🌍 Current UTC time: {utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Current Dubai time
    dubai_tz = pytz.timezone(Config.TIMEZONE)
    dubai_now = datetime.now(dubai_tz)
    print(f"🇦🇪 Current Dubai time: {dubai_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Current local server time
    local_now = datetime.now()
    print(f"🖥️  Current server time: {local_now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return utc_now, dubai_now, local_now

def get_next_scheduled_runs():
    """Calculate next scheduled runs"""
    print("\n📅 NEXT SCHEDULED RUNS")
    print("=" * 50)
    
    utc_now = datetime.now(pytz.UTC)
    
    # Define scheduled tasks (matching peekr_automation_master.py)
    scheduled_tasks = [
        # Lead Generation (Email Fetching)
        {'name': 'Lead Generation (Email Fetching)', 'day': 5, 'hour': 20, 'minute': 0},  # Saturday 20:00 UTC = Sunday 00:00 Dubai
        {'name': 'Lead Generation (Email Fetching)', 'day': 1, 'hour': 20, 'minute': 0},  # Tuesday 20:00 UTC = Wednesday 00:00 Dubai
        
        # Email Outreach  
        {'name': 'Email Outreach', 'day': 0, 'hour': 4, 'minute': 0},   # Monday 04:00 UTC = Monday 08:00 Dubai
        {'name': 'Email Outreach', 'day': 3, 'hour': 4, 'minute': 0},   # Thursday 04:00 UTC = Thursday 08:00 Dubai
        
        # Follow-up Campaigns
        {'name': 'Follow-up Campaigns', 'day': 0, 'hour': 7, 'minute': 0},  # Monday 07:00 UTC = Monday 11:00 Dubai
    ]
    
    next_runs = {}
    
    for task in scheduled_tasks:
        # Calculate next occurrence
        next_run_utc = get_next_occurrence(utc_now, task['day'], task['hour'], task['minute'])
        
        # Convert to Dubai time
        dubai_tz = pytz.timezone(Config.TIMEZONE)
        next_run_dubai = next_run_utc.astimezone(dubai_tz)
        
        # Calculate time remaining
        time_remaining = next_run_utc - utc_now
        
        task_name = task['name']
        
        # Keep the earliest next run for each task type
        if task_name not in next_runs or next_run_utc < next_runs[task_name]['utc_time']:
            next_runs[task_name] = {
                'utc_time': next_run_utc,
                'dubai_time': next_run_dubai,
                'time_remaining': time_remaining
            }
    
    # Display next runs with emojis
    task_emojis = {
        'Lead Generation (Email Fetching)': '📊',
        'Email Outreach': '📧',
        'Follow-up Campaigns': '🔄'
    }
    
    for task_name, info in next_runs.items():
        emoji = task_emojis.get(task_name, '📋')
        print(f"\n{emoji} {task_name}:")
        print(f"   ⏰ Next run (Dubai): {info['dubai_time'].strftime('%A, %B %d at %I:%M %p %Z')}")
        print(f"   🌍 Next run (UTC): {info['utc_time'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Format time remaining
        total_seconds = int(info['time_remaining'].total_seconds())
        if total_seconds < 0:
            print(f"   ⚠️  OVERDUE by {format_duration(-total_seconds)}")
        else:
            print(f"   ⏳ Time remaining: {format_duration(total_seconds)}")

def get_next_occurrence(current_time, target_day, target_hour, target_minute):
    """Calculate next occurrence of a weekly scheduled task"""
    # target_day: 0=Monday, 1=Tuesday, ..., 6=Sunday
    current_weekday = current_time.weekday()
    
    # Calculate days until target day
    days_ahead = target_day - current_weekday
    if days_ahead < 0:  # Target day already happened this week
        days_ahead += 7
    elif days_ahead == 0:  # Target day is today
        # Check if target time has already passed today
        target_time_today = current_time.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        if current_time >= target_time_today:
            days_ahead = 7  # Next occurrence is next week
    
    next_occurrence = current_time + timedelta(days=days_ahead)
    next_occurrence = next_occurrence.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    
    return next_occurrence

def format_duration(seconds):
    """Format duration in human readable format"""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minutes"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"

def check_process_running():
    """Check if automation processes are running"""
    print("\n🔍 PROCESS STATUS")
    print("=" * 50)
    
    automation_processes = []
    dashboard_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
            
            # Check for automation processes
            if any(script in cmdline for script in [
                'peekr_automation_master.py',
                'combined_app.py'
            ]):
                automation_processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cmdline': cmdline,
                    'uptime': datetime.now() - datetime.fromtimestamp(proc.info['create_time'])
                })
            
            # Check for dashboard processes
            elif 'streamlit' in cmdline and 'admin_dashboard.py' in cmdline:
                dashboard_processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cmdline': cmdline,
                    'uptime': datetime.now() - datetime.fromtimestamp(proc.info['create_time'])
                })
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Display automation processes
    if automation_processes:
        print("✅ AUTOMATION ENGINE STATUS: RUNNING")
        for proc in automation_processes:
            print(f"   🤖 PID {proc['pid']}: {proc['name']}")
            print(f"      📝 Command: {proc['cmdline'][:80]}...")
            print(f"      ⏰ Uptime: {format_duration(int(proc['uptime'].total_seconds()))}")
    else:
        print("❌ AUTOMATION ENGINE STATUS: NOT RUNNING")
        print("   💡 The automation engine is not active!")
        print("   🔧 Expected processes: peekr_automation_master.py or combined_app.py")
    
    # Display dashboard processes
    print(f"\n📊 DASHBOARD STATUS: {'RUNNING' if dashboard_processes else 'NOT RUNNING'}")
    for proc in dashboard_processes:
        print(f"   🖥️  PID {proc['pid']}: Streamlit Dashboard")
        print(f"      ⏰ Uptime: {format_duration(int(proc['uptime'].total_seconds()))}")

def check_log_files():
    """Check recent log entries"""
    print("\n📋 RECENT LOG ACTIVITY")
    print("=" * 50)
    
    log_file = "peekr_automation.log"
    
    if os.path.exists(log_file):
        try:
            # Get last 10 lines of log file
            with open(log_file, 'r') as f:
                lines = f.readlines()
                recent_lines = lines[-10:] if len(lines) >= 10 else lines
            
            if recent_lines:
                print(f"📄 Last {len(recent_lines)} log entries from {log_file}:")
                print("-" * 30)
                for line in recent_lines:
                    print(f"   {line.strip()}")
            else:
                print("📄 Log file exists but is empty")
                
            # Check file modification time
            mod_time = datetime.fromtimestamp(os.path.getmtime(log_file))
            time_since_update = datetime.now() - mod_time
            print(f"\n⏰ Log last updated: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   ({format_duration(int(time_since_update.total_seconds()))} ago)")
            
        except Exception as e:
            print(f"❌ Error reading log file: {e}")
    else:
        print(f"❌ Log file '{log_file}' not found")
        print("   💡 This might indicate the automation engine hasn't started yet")

def check_email_monitoring_stats():
    """Check if real-time email monitoring is working"""
    print("\n📡 EMAIL MONITORING STATUS")
    print("=" * 50)
    
    # Try to connect to email server to test monitoring capability
    try:
        import imaplib
        import socket
        
        # Test DNS resolution
        socket.gethostbyname(Config.IMAP_SERVER)
        
        # Test IMAP connection
        mail = imaplib.IMAP4_SSL(Config.IMAP_SERVER, Config.IMAP_PORT)
        mail.login(Config.EMAIL_ACCOUNT, Config.EMAIL_PASSWORD)
        mail.select("inbox")
        
        # Get recent emails count
        result, data = mail.search(None, "ALL")
        if result == 'OK':
            email_count = len(data[0].split())
            print(f"✅ Email monitoring capability: ACTIVE")
            print(f"   📧 Total emails in inbox: {email_count}")
            print(f"   🔗 Connected to: {Config.IMAP_SERVER}:{Config.IMAP_PORT}")
            print(f"   👤 Account: {Config.EMAIL_ACCOUNT}")
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"❌ Email monitoring capability: FAILED")
        print(f"   Error: {e}")

def check_google_sheets_connectivity():
    """Check Google Sheets connectivity"""
    print("\n📊 GOOGLE SHEETS STATUS")
    print("=" * 50)
    
    try:
        from credentials_helper import get_google_sheets_client
        gc = get_google_sheets_client()
        sheet = gc.open_by_key(Config.SPREADSHEET_ID)
        
        print("✅ Google Sheets connectivity: ACTIVE")
        print(f"   📄 Spreadsheet: {sheet.title}")
        print(f"   🔗 Sheet ID: {Config.SPREADSHEET_ID}")
        
        # Check worksheets
        try:
            incoming_leads = sheet.worksheet("Incoming Leads")
            data = incoming_leads.get_all_records()
            print(f"   📋 'Incoming Leads' worksheet: {len(data)} records")
        except:
            print("   ⚠️ 'Incoming Leads' worksheet: NOT ACCESSIBLE")
            
    except Exception as e:
        print(f"❌ Google Sheets connectivity: FAILED")
        print(f"   Error: {e}")

def main():
    """Run complete automation status check"""
    print("🚀 PEEKR AUTOMATION STATUS CHECKER")
    print("=" * 60)
    
    # Get time information
    get_server_time_info()
    
    # Check process status
    check_process_running()
    
    # Get next scheduled runs
    get_next_scheduled_runs()
    
    # Check log files
    check_log_files()
    
    # Check email monitoring
    check_email_monitoring_stats()
    
    # Check Google Sheets
    check_google_sheets_connectivity()
    
    print("\n" + "=" * 60)
    print("📊 STATUS CHECK COMPLETE")
    print("=" * 60)
    
    # Summary recommendations
    print("\n💡 RECOMMENDATIONS:")
    print("-" * 30)
    
    # Check if automation is running (with error handling)
    automation_running = False
    try:
        for proc in psutil.process_iter(['cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and ('peekr_automation_master.py' in str(cmdline) or 'combined_app.py' in str(cmdline)):
                    automation_running = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception:
        pass
    
    if not automation_running:
        print("❌ CRITICAL: Automation engine is not running!")
        print("   🔧 Start it with: python3 peekr_automation_master.py")
        print("   🔧 Or combined mode: python3 combined_app.py")
    else:
        print("✅ Automation engine is running")
        
    # Check log activity
    if os.path.exists("peekr_automation.log"):
        mod_time = datetime.fromtimestamp(os.path.getmtime("peekr_automation.log"))
        if datetime.now() - mod_time > timedelta(minutes=10):
            print("⚠️  Log file hasn't been updated recently - check if automation is active")
    
    print("\n🔄 Run this script regularly to monitor your automation status!")

if __name__ == "__main__":
    main()
