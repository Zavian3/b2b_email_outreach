#!/usr/bin/env python3
"""
Peekr B2B Lead Generation - Advanced Admin Dashboard
===============================================

Comprehensive admin interface for monitoring and managing the B2B automation system.
Features:
- Real-time analytics and insights
- Lead management and filtering
- Campaign performance tracking  
- Dynamic prompt editing
- System status monitoring
- Export capabilities
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import gspread
import json
import os
from datetime import datetime, timedelta
import time
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import io
import subprocess
import psutil
import glob
import requests

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Peekr B2B Admin Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apple Design System inspired CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@100;200;300;400;500;600;700;800;900&family=SF+Pro+Text:wght@100;200;300;400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;600;700;800;900&display=swap');
    
    /* Root variables - Apple inspired */
    :root {
        --color-bg-primary: #000000;
        --color-bg-secondary: #1c1c1e;
        --color-bg-tertiary: #2c2c2e;
        --color-bg-quaternary: #3a3a3c;
        --color-text-primary: #ffffff;
        --color-text-secondary: #ebebf5;
        --color-text-tertiary: #ebebf599;
        --color-accent: #007aff;
        --color-accent-hover: #0051d5;
        --color-success: #30d158;
        --color-warning: #ff9f0a;
        --color-danger: #ff453a;
        --shadow-small: 0 1px 3px rgba(0, 0, 0, 0.4);
        --shadow-medium: 0 4px 16px rgba(0, 0, 0, 0.3);
        --shadow-large: 0 8px 32px rgba(0, 0, 0, 0.4);
        --border-radius-small: 8px;
        --border-radius-medium: 12px;
        --border-radius-large: 16px;
        --transition-smooth: all 0.2s cubic-bezier(0.4, 0.0, 0.2, 1);
    }
    
    .stApp {
        font-family: 'SF Pro Text', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(180deg, var(--color-bg-primary) 0%, var(--color-bg-secondary) 100%);
        color: var(--color-text-primary);
        line-height: 1.47059;
        letter-spacing: -0.022em;
    }
    
    /* Typography - Apple style */
    .main-header {
        font-family: 'SF Pro Display', 'Inter', sans-serif;
        font-size: 2.75rem;
        font-weight: 700;
        color: var(--color-text-primary);
        text-align: center;
        margin: 2rem 0 3rem 0;
        letter-spacing: -0.05em;
        line-height: 1.1;
    }
    
    .section-header {
        font-family: 'SF Pro Display', 'Inter', sans-serif;
        font-size: 1.375rem;
        font-weight: 600;
        color: var(--color-text-primary);
        margin: 3rem 0 1.5rem 0;
        letter-spacing: -0.03em;
        line-height: 1.2;
    }
    
    /* Refined metric cards */
    .metric-card {
        background: var(--color-bg-tertiary);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        padding: 1.5rem;
        border-radius: var(--border-radius-large);
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin: 0.75rem 0;
        transition: var(--transition-smooth);
        box-shadow: var(--shadow-small);
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-medium);
        border-color: rgba(255, 255, 255, 0.2);
        background: var(--color-bg-quaternary);
    }
    
    .metric-title {
        font-size: 0.8125rem;
        color: var(--color-text-tertiary);
        font-weight: 500;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    
    .metric-value {
        font-family: 'SF Pro Display', 'Inter', sans-serif;
        font-size: 2.25rem;
        font-weight: 700;
        color: var(--color-text-primary);
        line-height: 1;
        letter-spacing: -0.04em;
        margin-bottom: 0.25rem;
    }
    
    .metric-change {
        font-size: 0.8125rem;
        font-weight: 500;
        letter-spacing: 0.01em;
    }
    
    /* Apple color system */
    .positive { color: var(--color-success); }
    .negative { color: var(--color-danger); }
    .neutral { color: var(--color-text-tertiary); }
    
    /* Refined status badges */
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 100px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
    }
    
    .status-active { 
        background: rgba(48, 209, 88, 0.15); 
        color: var(--color-success); 
        border: 1px solid rgba(48, 209, 88, 0.3);
    }
    .status-pending { 
        background: rgba(255, 159, 10, 0.15); 
        color: var(--color-warning); 
        border: 1px solid rgba(255, 159, 10, 0.3);
    }
    .status-inactive { 
        background: rgba(255, 69, 58, 0.15); 
        color: var(--color-danger); 
        border: 1px solid rgba(255, 69, 58, 0.3);
    }
    
    /* Apple-style buttons */
    .stButton > button {
        background: var(--color-accent);
        color: white;
        border: none;
        border-radius: var(--border-radius-medium);
        padding: 0.75rem 1.5rem;
        font-family: 'SF Pro Text', 'Inter', sans-serif;
        font-weight: 500;
        font-size: 0.9375rem;
        letter-spacing: -0.01em;
        transition: var(--transition-smooth);
        box-shadow: var(--shadow-small);
        cursor: pointer;
    }
    
    .stButton > button:hover {
        background: var(--color-accent-hover);
        transform: translateY(-1px);
        box-shadow: var(--shadow-medium);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: var(--shadow-small);
    }
    
    /* Refined sidebar */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: var(--color-bg-secondary);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Enhanced tables */
    .dataframe {
        background: var(--color-bg-tertiary) !important;
        color: var(--color-text-primary) !important;
        border-radius: var(--border-radius-medium);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: var(--shadow-small);
    }
    
    /* Apple-style tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: var(--color-bg-tertiary);
        padding: 4px;
        border-radius: var(--border-radius-medium);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--color-text-tertiary);
        border-radius: var(--border-radius-small);
        padding: 0.5rem 1rem;
        font-weight: 500;
        font-size: 0.9375rem;
        border: none;
        transition: var(--transition-smooth);
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--color-accent);
        color: white;
        box-shadow: var(--shadow-small);
    }
    
    /* Log viewer */
    .log-container {
        background: var(--color-bg-primary);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: var(--border-radius-medium);
        padding: 1rem;
        font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
        font-size: 0.8125rem;
        line-height: 1.4;
        max-height: 400px;
        overflow-y: auto;
        box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.3);
    }
    
    .log-entry {
        margin-bottom: 0.25rem;
        padding: 0.25rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .log-timestamp {
        color: var(--color-text-tertiary);
        font-weight: 500;
    }
    
    .log-level-info { color: var(--color-accent); }
    .log-level-warning { color: var(--color-warning); }
    .log-level-error { color: var(--color-danger); }
    .log-level-success { color: var(--color-success); }
    
    /* Component status indicators */
    .component-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        transition: var(--transition-smooth);
    }
    
    .component-row:hover {
        background: rgba(255, 255, 255, 0.02);
        border-radius: var(--border-radius-small);
    }
    
    .component-name {
        font-weight: 500;
        color: var(--color-text-primary);
    }
    
    .component-description {
        font-size: 0.8125rem;
        color: var(--color-text-tertiary);
        margin-top: 0.125rem;
    }
    
    /* Enhanced alerts */
    .stSuccess { 
        background: rgba(48, 209, 88, 0.1); 
        border: 1px solid rgba(48, 209, 88, 0.3); 
        border-radius: var(--border-radius-medium);
    }
    .stError { 
        background: rgba(255, 69, 58, 0.1); 
        border: 1px solid rgba(255, 69, 58, 0.3); 
        border-radius: var(--border-radius-medium);
    }
    .stWarning { 
        background: rgba(255, 159, 10, 0.1); 
        border: 1px solid rgba(255, 159, 10, 0.3); 
        border-radius: var(--border-radius-medium);
    }
    .stInfo { 
        background: rgba(0, 122, 255, 0.1); 
        border: 1px solid rgba(0, 122, 255, 0.3); 
        border-radius: var(--border-radius-medium);
    }
    
    /* Glassmorphism effect */
    .glass-card {
        background: rgba(44, 44, 46, 0.8);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: var(--border-radius-large);
        box-shadow: var(--shadow-medium);
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--color-bg-tertiary);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.3);
    }
</style>
""", unsafe_allow_html=True)

class AdminDashboard:
    def __init__(self):
        self.setup_session_state()
        self.load_configuration()
    
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = None
        if 'selected_leads' not in st.session_state:
            st.session_state.selected_leads = []
    
    def load_configuration(self):
        """Load configuration from environment"""
        self.spreadsheet_id = os.getenv('SPREADSHEET_ID', '1_SlKC3SkL90lYf2i_lELZrZQvh2tdMUaZSKe5_nG4WQ')
        self.prompts_dir = 'prompts'
    
    @st.cache_data(show_spinner=False)
    def load_google_sheets_data(_self):
        """Load data from Google Sheets with proper error handling"""
        try:
            # Get credentials
            if os.getenv("GOOGLE_CREDENTIALS_FILE"):
                # Use local credentials file
                scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                creds = Credentials.from_service_account_file(os.getenv("GOOGLE_CREDENTIALS_FILE"), scopes=scope)
            else:
                raise ValueError("Google credentials not found")
            
            client = gspread.authorize(creds)
            
            # Load data from both sheets
            spreadsheet = client.open_by_key(_self.spreadsheet_id)
            leads_sheet = spreadsheet.worksheet("Incoming Leads")
            categories_sheet = spreadsheet.worksheet("Categories")
            
            leads_data = leads_sheet.get_all_records()
            categories_data = categories_sheet.get_all_records()
            
            leads_df = pd.DataFrame(leads_data)
            categories_df = pd.DataFrame(categories_data)
            
            # Clean and process data
            leads_df = _self.clean_leads_data(leads_df)
            
            return leads_df, categories_df
            
        except Exception as e:
            st.error(f"❌ Error loading data from Google Sheets: {str(e)}")
            return pd.DataFrame(), pd.DataFrame()
    
    def clean_leads_data(self, df):
        """Clean and standardize the leads data"""
        if df.empty:
            return df
        
        # Standardize column names and handle missing values
        df = df.fillna('')
        
        # Convert dates
        date_columns = ['Mail Send at', 'Last Follow-up Date', 'Reply Date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Standardize status values
        if 'Status' in df.columns:
            df['Status'] = df['Status'].str.strip().str.title()
        
        return df
    
    def load_prompts(self):
        """Load all prompt files from the prompts directory"""
        prompts = {}
        try:
            if os.path.exists(self.prompts_dir):
                for filename in os.listdir(self.prompts_dir):
                    if filename.endswith('.txt'):
                        filepath = os.path.join(self.prompts_dir, filename)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            prompts[filename] = f.read()
            return prompts
        except Exception as e:
            st.error(f"Error loading prompts: {e}")
            return {}
    
    def save_prompt(self, filename, content):
        """Save prompt content to file"""
        try:
            filepath = os.path.join(self.prompts_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            st.error(f"Error saving prompt: {e}")
            return False
    
    def check_component_status(self):
        """Check actual status of system components"""
        components = {}
        
        # Check if main automation script exists and is accessible
        main_script = 'peekr_automation_master.py'
        components['automation_script'] = {
            'name': '🤖 Automation Engine',
            'description': 'Core automation system',
            'status': 'active' if os.path.exists(main_script) else 'inactive'
        }
        
        # Check Google Sheets connectivity
        try:
            # Quick connectivity test
            if os.getenv("GOOGLE_CREDENTIALS_FILE"):
                components['google_sheets'] = {
                    'name': '📋 Google Sheets Integration',
                    'description': 'Data storage and synchronization',
                    'status': 'active'
                }
            else:
                components['google_sheets'] = {
                    'name': '📋 Google Sheets Integration',
                    'description': 'Credentials not configured',
                    'status': 'inactive'
                }
        except Exception:
            components['google_sheets'] = {
                'name': '📋 Google Sheets Integration',
                'description': 'Connection unavailable',
                'status': 'inactive'
            }
        
        # Check OpenAI API key
        openai_key = os.getenv('OPENAI_API_KEY')
        components['openai'] = {
            'name': '🧠 AI Content Generation',
            'description': 'OpenAI integration for personalized messaging',
            'status': 'active' if openai_key and len(openai_key) > 10 else 'inactive'
        }
        
        # Check Apify API key
        apify_key = os.getenv('APIFY_API_KEY')
        components['apify'] = {
            'name': '🔍 Lead Generation Service',
            'description': 'Apify integration for prospect discovery',
            'status': 'active' if apify_key and len(apify_key) > 10 else 'inactive'
        }
        
        # Check email configuration
        email_account = os.getenv('EMAIL_ACCOUNT')
        email_password = os.getenv('EMAIL_PASSWORD')
        components['email_service'] = {
            'name': '📧 Email Infrastructure',
            'description': 'SMTP and IMAP communication services',
            'status': 'active' if email_account and email_password else 'inactive'
        }
        
        # Check prompt files
        prompt_files_exist = os.path.exists(self.prompts_dir) and len(os.listdir(self.prompts_dir)) > 0
        components['prompts'] = {
            'name': '📝 Content Templates',
            'description': 'AI prompt templates and messaging framework',
            'status': 'active' if prompt_files_exist else 'inactive'
        }
        
        # Check log file (indicates recent activity)
        log_files = glob.glob('*.log')
        recent_activity = False
        if log_files:
            for log_file in log_files:
                try:
                    file_time = os.path.getmtime(log_file)
                    if datetime.now().timestamp() - file_time < 3600:  # Activity in last hour
                        recent_activity = True
                        break
                except:
                    pass
        
        components['monitoring'] = {
            'name': '📡 Activity Monitoring',
            'description': 'Recent system activity detected' if recent_activity else 'No recent system activity',
            'status': 'active' if recent_activity else 'pending'
        }
        
        return components
    
    def get_system_logs(self, max_lines=100):
        """Get recent system logs"""
        logs = []
        log_files = glob.glob('*.log')
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in reversed(lines[-max_lines:]):  # Get last max_lines
                        if line.strip():
                            logs.append({
                                'timestamp': self.extract_timestamp(line),
                                'level': self.extract_log_level(line),
                                'message': line.strip(),
                                'file': log_file
                            })
            except Exception as e:
                logs.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'level': 'error',
                    'message': f'Error reading {log_file}: {str(e)}',
                    'file': 'system'
                })
        
        # Sort by timestamp (most recent first)
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        return logs[:max_lines]
    
    def extract_timestamp(self, log_line):
        """Extract timestamp from log line"""
        try:
            # Look for timestamp pattern: YYYY-MM-DD HH:MM:SS
            import re
            pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
            match = re.search(pattern, log_line)
            if match:
                return match.group(1)
            else:
                return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        except:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def extract_log_level(self, log_line):
        """Extract log level from log line"""
        log_line_upper = log_line.upper()
        if 'ERROR' in log_line_upper or '❌' in log_line:
            return 'error'
        elif 'WARNING' in log_line_upper or 'WARN' in log_line_upper or '⚠️' in log_line:
            return 'warning'
        elif 'SUCCESS' in log_line_upper or '✅' in log_line:
            return 'success'
        elif 'INFO' in log_line_upper:
            return 'info'
        else:
            return 'info'

def render_header():
    """Render the main header"""
    st.markdown('<h1 class="main-header">🎯 Peekr B2B Admin Dashboard</h1>', unsafe_allow_html=True)
    
    # Subtitle and refresh button layout
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("**Advanced Analytics & Management Interface**")
        st.markdown(f"*Last updated: {st.session_state.last_refresh.strftime('%H:%M:%S') if st.session_state.last_refresh else 'Never'}*")
    with col2:
        if st.button("🔄 Refresh Data", type="primary"):
            st.cache_data.clear()
            st.session_state.last_refresh = datetime.now()
            st.rerun()

def render_overview_metrics(leads_df, categories_df):
    """Render overview metrics cards"""
    st.markdown('<div class="section-header">📊 Overview Metrics</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Calculate metrics
    total_leads = len(leads_df)
    valid_emails = len(leads_df[leads_df['Valid Email'] != ''])
    emails_sent = len(leads_df[leads_df['Status'] == 'Sent'])
    responses_received = len(leads_df[leads_df['Mail Received'] == 'YES'])
    active_campaigns = len(categories_df)
    
    # Response rate
    response_rate = (responses_received / emails_sent * 100) if emails_sent > 0 else 0
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📈 Total Leads</div>
            <div class="metric-value">{total_leads:,}</div>
            <div class="metric-change neutral">Active in system</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        email_rate = (valid_emails / total_leads * 100) if total_leads > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📧 Valid Emails</div>
            <div class="metric-value">{valid_emails:,}</div>
            <div class="metric-change {'positive' if email_rate > 50 else 'neutral'}">{email_rate:.1f}% coverage</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📤 Emails Sent</div>
            <div class="metric-value">{emails_sent:,}</div>
            <div class="metric-change neutral">Outreach campaigns</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📬 Responses</div>
            <div class="metric-value">{responses_received:,}</div>
            <div class="metric-change {'positive' if response_rate > 5 else 'negative'}">{response_rate:.1f}% response rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🎯 Active Campaigns</div>
            <div class="metric-value">{active_campaigns}</div>
            <div class="metric-change neutral">Categories running</div>
        </div>
        """, unsafe_allow_html=True)

def render_performance_analytics(leads_df):
    """Render performance analytics charts"""
    st.markdown('<div class="section-header">📈 Performance Analytics</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Email funnel chart
        if not leads_df.empty:
            funnel_data = {
                'Stage': ['Total Leads', 'Valid Emails', 'Emails Sent', 'Responses', 'Interested'],
                'Count': [
                    len(leads_df),
                    len(leads_df[leads_df['Valid Email'] != '']),
                    len(leads_df[leads_df['Status'] == 'Sent']),
                    len(leads_df[leads_df['Mail Received'] == 'YES']),
                    len(leads_df[leads_df['Reply Received'] == 'INTERESTED'])
                ]
            }
            
            fig = px.funnel(pd.DataFrame(funnel_data), x='Count', y='Stage',
                          title='📊 Lead Conversion Funnel',
                          color_discrete_sequence=['#60a5fa'])
            fig.update_layout(height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Status distribution
        if not leads_df.empty and 'Status' in leads_df.columns:
            status_counts = leads_df['Status'].value_counts()
            
            fig = px.pie(values=status_counts.values, names=status_counts.index,
                        title='📋 Lead Status Distribution',
                        color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

def render_campaign_performance(leads_df):
    """Render campaign performance by category"""
    if leads_df.empty or 'Category' not in leads_df.columns:
        return
    
    st.markdown('<div class="section-header">🎯 Campaign Performance by Category</div>', unsafe_allow_html=True)
    
    # Calculate performance metrics by category
    category_stats = []
    for category in leads_df['Category'].unique():
        if category:
            cat_df = leads_df[leads_df['Category'] == category]
            stats = {
                'Category': category,
                'Total Leads': len(cat_df),
                'Valid Emails': len(cat_df[cat_df['Valid Email'] != '']),
                'Emails Sent': len(cat_df[cat_df['Status'] == 'Sent']),
                'Responses': len(cat_df[cat_df['Mail Received'] == 'YES']),
                'Response Rate': len(cat_df[cat_df['Mail Received'] == 'YES']) / len(cat_df[cat_df['Status'] == 'Sent']) * 100 if len(cat_df[cat_df['Status'] == 'Sent']) > 0 else 0
            }
            category_stats.append(stats)
    
    if category_stats:
        cat_df = pd.DataFrame(category_stats)
        
        # Create comparison chart
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Bar(x=cat_df['Category'], y=cat_df['Emails Sent'], name='Emails Sent', marker_color='#60a5fa'),
            secondary_y=False,
        )
        
        fig.add_trace(
            go.Scatter(x=cat_df['Category'], y=cat_df['Response Rate'], mode='lines+markers',
                      name='Response Rate (%)', marker_color='#34d399'),
            secondary_y=True,
        )
        
        fig.update_xaxes(title_text="Category")
        fig.update_yaxes(title_text="Emails Sent", secondary_y=False)
        fig.update_yaxes(title_text="Response Rate (%)", secondary_y=True)
        fig.update_layout(title_text="📊 Category Performance Overview", height=500)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance table
        st.dataframe(cat_df, use_container_width=True, height=300)

def render_leads_management(leads_df):
    """Render leads management interface"""
    st.markdown('<div class="section-header">👥 Leads Management</div>', unsafe_allow_html=True)
    
    if leads_df.empty:
        st.warning("No leads data available.")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Filter by status
        status_options = ['All'] + list(leads_df['Status'].unique())
        selected_status = st.selectbox("🏷️ Filter by Status", status_options)
    
    with col2:
        # Filter by category
        category_options = ['All'] + list(leads_df['Category'].unique())
        selected_category = st.selectbox("📂 Filter by Category", category_options)
    
    with col3:
        # Filter by location
        location_options = ['All'] + list(leads_df['Location'].unique())
        selected_location = st.selectbox("📍 Filter by Location", location_options)
    
    with col4:
        # Export options
        if st.button("📤 Export Filtered Data"):
            # Create filtered dataframe for export
            filtered_df = leads_df.copy()
            
            if selected_status != 'All':
                filtered_df = filtered_df[filtered_df['Status'] == selected_status]
            if selected_category != 'All':
                filtered_df = filtered_df[filtered_df['Category'] == selected_category]
            if selected_location != 'All':
                filtered_df = filtered_df[filtered_df['Location'] == selected_location]
            
            # Convert to CSV
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    # Apply filters
    filtered_df = leads_df.copy()
    
    if selected_status != 'All':
        filtered_df = filtered_df[filtered_df['Status'] == selected_status]
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['Category'] == selected_category]
    if selected_location != 'All':
        filtered_df = filtered_df[filtered_df['Location'] == selected_location]
    
    # Display filtered results
    st.markdown(f"**Showing {len(filtered_df)} of {len(leads_df)} leads**")
    
    # Enhanced dataframe with formatting
    if not filtered_df.empty:
        # Select key columns for display
        display_columns = ['Title', 'Valid Email', 'Category', 'Location', 'Status', 'Mail Send at', 'Mail Received', 'Phone']
        available_columns = [col for col in display_columns if col in filtered_df.columns]
        
        # Create display-friendly column names
        column_name_mapping = {
            'Mail Send at': 'Mail Sent At',
            'Valid Email': 'Valid Email',
            'Mail Received': 'Mail Received',
            'Last Follow-up Date': 'Last Follow-up Date'
        }
        
        display_df = filtered_df[available_columns].copy()
        
        # Rename columns for better display
        display_df = display_df.rename(columns=column_name_mapping)
        
        # Format the dataframe
        for col in display_df.columns:
            if display_df[col].dtype == 'object':
                display_df[col] = display_df[col].astype(str)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=500,
            column_config={
                "Status": st.column_config.TextColumn(
                    "Status",
                    help="Current lead status"
                ),
                "Valid Email": st.column_config.TextColumn(
                    "Valid Email",
                    help="Validated business email"
                ),
                "Phone": st.column_config.TextColumn(
                    "Phone",
                    help="Contact phone number"
                ),
                "Mail Sent At": st.column_config.TextColumn(
                    "Mail Sent At",
                    help="Date email was sent"
                )
            }
        )

def render_logs_viewer(dashboard):
    """Render real-time logs viewer"""
    st.markdown('<div class="section-header">📋 System Logs</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        log_lines = st.selectbox("📄 Lines to show", [50, 100, 200, 500], index=1)
    
    with col2:
        log_level_filter = st.selectbox("🏷️ Filter by level", ["All", "Error", "Warning", "Info", "Success"])
    
    with col3:
        auto_refresh = st.checkbox("🔄 Auto-refresh (10s)", value=False)
    
    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(10)
        st.rerun()
    
    # Get logs
    logs = dashboard.get_system_logs(log_lines)
    
    # Filter by log level
    if log_level_filter != "All":
        logs = [log for log in logs if log['level'].lower() == log_level_filter.lower()]
    
    if not logs:
        st.warning("🔍 No logs found matching the current filters.")
        return
    
    # Display logs in a container
    st.markdown("**📋 Recent System Activity:**")
    
    log_container = st.container()
    with log_container:
        log_html = '<div class="log-container">'
        
        for log in logs:
            level_class = f"log-level-{log['level']}"
            timestamp_formatted = log['timestamp']
            message_escaped = log['message'].replace('<', '&lt;').replace('>', '&gt;')
            
            log_html += f"""
            <div class="log-entry">
                <span class="log-timestamp">[{timestamp_formatted}]</span>
                <span class="{level_class}">[{log['level'].upper()}]</span>
                <span>{message_escaped}</span>
            </div>
            """
        
        log_html += '</div>'
        st.markdown(log_html, unsafe_allow_html=True)
    
    # Log statistics
    st.markdown("**📊 Log Summary:**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    level_counts = {}
    for log in logs:
        level = log['level']
        level_counts[level] = level_counts.get(level, 0) + 1
    
    with col1:
        error_count = level_counts.get('error', 0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🚨 Errors</div>
            <div class="metric-value" style="color: var(--color-danger);">{error_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        warning_count = level_counts.get('warning', 0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">⚠️ Warnings</div>
            <div class="metric-value" style="color: var(--color-warning);">{warning_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        info_count = level_counts.get('info', 0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">ℹ️ Info</div>
            <div class="metric-value" style="color: var(--color-accent);">{info_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        success_count = level_counts.get('success', 0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">✅ Success</div>
            <div class="metric-value" style="color: var(--color-success);">{success_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Export functionality
    if st.button("📤 Export Current View"):
        filtered_log_text = "\n".join([
            f"[{log['timestamp']}] {log['level'].upper()}: {log['message']}" 
            for log in logs
        ])
        
        st.download_button(
            label="📥 Download Filtered Logs",
            data=filtered_log_text,
            file_name=f"filtered_logs_{log_level_filter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

def render_prompt_management(dashboard):
    """Render prompt management interface"""
    st.markdown('<div class="section-header">📝 Prompt Management</div>', unsafe_allow_html=True)
    
    st.markdown("""
    **Manage AI prompts used throughout the automation system.**  
    Changes are saved directly to the prompt files and will be used immediately.
    """)
    
    # Load current prompts
    prompts = dashboard.load_prompts()
    
    if not prompts:
        st.warning("No prompt files found in the prompts directory.")
        return
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**Available Prompts:**")
        
        # Create display-friendly prompt names
        prompt_display_names = {}
        for filename in prompts.keys():
            display_name = filename.replace('_', ' ').replace('.txt', '').title()
            display_name = display_name.replace('Prompt', 'Template')
            prompt_display_names[display_name] = filename
        
        selected_display_name = st.selectbox(
            "Select prompt to edit:",
            list(prompt_display_names.keys()),
            help="Choose a prompt file to view and edit"
        )
        
        selected_prompt = prompt_display_names[selected_display_name]
    
    with col2:
        if selected_prompt:
            st.markdown(f"**Editing: {selected_display_name}**")
            
            # Display current prompt content
            current_content = prompts[selected_prompt]
            
            # Text area for editing
            edited_content = st.text_area(
                "Prompt Content:",
                value=current_content,
                height=400,
                help="Edit the prompt content. Use placeholder variables like {{Title}}, {{Category}}, etc."
            )
            
            col1_btn, col2_btn, col3_btn = st.columns(3)
            
            with col1_btn:
                if st.button("💾 Save Changes", type="primary"):
                    if dashboard.save_prompt(selected_prompt, edited_content):
                        st.success(f"✅ {selected_prompt} saved successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to save prompt")
            
            with col2_btn:
                if st.button("🔄 Reset"):
                    st.rerun()
            
            with col3_btn:
                if st.button("📋 Copy"):
                    st.code(current_content, language="text")
    
    # Prompt usage guide
    with st.expander("📖 Prompt Usage Guide", expanded=False):
        st.markdown("""
        ### Available Prompt Files:
        
        - **`get_subject_prompt.txt`**: Email subject line generation
        - **`classify_prompt.txt`**: Interest level classification  
        - **`generate_interested_reply_prompt.txt`**: Response for interested leads
        - **`generate_not_interested_reply_prompt.txt`**: Response for uninterested leads
        - **`generate_followup_prompt.txt`**: Follow-up email generation
        
        ### Available Variables:
        
        - `{{Title}}`: Company/lead name
        - `{{Category}}`: Business category
        - `{{Website}}`: Company website
        - `{{body}}`: Email body content
        - `{{solutions}}`: Solution suggestions
        
        ### Best Practices:
        
        1. **Be specific**: Clear, actionable prompts work best
        2. **Use context**: Include relevant business context
        3. **Test changes**: Monitor response rates after modifications
        4. **Backup**: Keep copies of working prompts before major changes
        """)

def render_system_status(dashboard):
    """Render system status and monitoring with real component checking"""
    st.markdown('<div class="section-header">⚙️ System Status</div>', unsafe_allow_html=True)
    
    # Get real component status
    components = dashboard.check_component_status()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔧 System Components:**")
        
        for component_key, component_data in components.items():
            status_class = f"status-{component_data['status']}"
            status_icon = "●" if component_data['status'] == 'active' else "○"
            
            st.markdown(f"""
            <div class="component-row">
                <div>
                    <div class="component-name">{component_data['name']}</div>
                    <div class="component-description">{component_data['description']}</div>
                </div>
                <span class="status-badge {status_class}">{status_icon} {component_data['status']}</span>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("**📅 Automation Schedule:**")
        
        schedule_items = [
            ("🌙 Lead Generation", "Sunday & Wednesday at 12:00 AM"),
            ("📧 Email Outreach", "Tuesday & Thursday at 11:00 AM"),
            ("🔄 Follow-up Campaigns", "Monday at 11:00 AM"),
            ("📡 Reply Monitoring", "24/7 Real-time")
        ]
        
        for task, schedule in schedule_items:
            st.markdown(f"""
            <div class="component-row">
                <div>
                    <div class="component-name">{task}</div>
                    <div class="component-description">{schedule}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Quick actions
    st.markdown("**⚡ Quick Actions:**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Refresh Status"):
            st.cache_data.clear()
            st.success("✅ System status refreshed!")
            st.rerun()
    
    with col2:
        if st.button("📊 Run Test Campaign"):
            st.info("🔧 Test campaign functionality available in production")
    
    with col3:
        if st.button("📧 Send Test Email"):
            st.info("🔧 Test email functionality available in production")
    
    with col4:
        if st.button("📋 Export Logs"):
            logs = dashboard.get_system_logs(500)
            if logs:
                log_text = "\n".join([f"[{log['timestamp']}] {log['level'].upper()}: {log['message']}" for log in logs])
                st.download_button(
                    label="📥 Download Logs",
                    data=log_text,
                    file_name=f"system_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            else:
                st.warning("No logs found")

def main():
    """Main dashboard application"""
    dashboard = AdminDashboard()
    
    # Render header
    render_header()
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        selected_tab = st.radio(
            "Choose section:",
            ["📊 Analytics", "👥 Leads", "📝 Prompts", "📋 Logs", "⚙️ System"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### 📈 Quick Stats")
        
        # Load data for sidebar stats
        with st.spinner("Loading data..."):
            leads_df, categories_df = dashboard.load_google_sheets_data()
        
        if not leads_df.empty:
            st.metric("Total Leads", len(leads_df))
            st.metric("Valid Emails", len(leads_df[leads_df['Valid Email'] != '']))
            st.metric("Active Categories", len(categories_df))
    
    # Main content based on selected tab
    if selected_tab == "📊 Analytics":
        render_overview_metrics(leads_df, categories_df)
        render_performance_analytics(leads_df)
        render_campaign_performance(leads_df)
        
    elif selected_tab == "👥 Leads":
        render_leads_management(leads_df)
        
    elif selected_tab == "📝 Prompts":
        render_prompt_management(dashboard)
        
    elif selected_tab == "📋 Logs":
        render_logs_viewer(dashboard)
        
    elif selected_tab == "⚙️ System":
        render_system_status(dashboard)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #64748b; padding: 2rem;'>
            <p><strong>Peekr B2B Lead Generation Dashboard</strong> | Advanced Analytics & Management</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main() 