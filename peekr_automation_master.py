#!/usr/bin/env python3
"""
PEEKR AUTOMATION MASTER - ALL-IN-ONE SYSTEM
============================================

This single file handles EVERYTHING:
1. Lead Generation (Apify) - Sunday & Wednesday midnight
2. Email Outreach - Tuesday & Thursday 11 AM  
3. Real-time Reply Monitoring - 24/7 instant responses
4. Follow-up Campaigns - Monday 11 AM (3-email limit)

Timezone configurable via TIMEZONE environment variable

Just run this ONE file on your server and everything is automated!
"""

import schedule
import time
import subprocess
import sys
import threading
import queue
import imaplib
import email
import smtplib
import gspread
import openai
import requests
import json
import hashlib
import logging
import pytz
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from oauth2client.service_account import ServiceAccountCredentials
from bs4 import BeautifulSoup
import markdown
import re
import pandas as pd
from config import Config
import socket
from requests.exceptions import ConnectionError, RequestException
from urllib3.exceptions import NameResolutionError
from prompt_loader import (
    get_subject_prompt,
    classify,
    generate_interested_reply,
    generate_not_interested_reply,
    generate_followup_prompt
)
from credentials_helper import get_google_sheets_client

# ==========================================
# LOGGING SETUP
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('peekr_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==========================================
# NETWORK UTILITIES
# ==========================================
def test_internet_connectivity():
    """Test basic internet connectivity"""
    # Test multiple reliable hosts
    test_hosts = ['8.8.8.8', '1.1.1.1', 'google.com']
    for host in test_hosts:
        try:
            socket.create_connection((host, 80), timeout=5).close()
            return True
        except (socket.gaierror, socket.timeout, OSError):
            continue
    return False

def retry_with_backoff(func, max_retries=3, backoff_factor=2, exceptions=(Exception,)):
    """Retry function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except exceptions as e:
            if attempt == max_retries - 1:
                raise e
            wait_time = backoff_factor ** attempt
            logger.warning(f"RETRY Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
    return None

# ==========================================
# PROMPT LOADING - Using External Files
# ==========================================
# Note: Prompt functions are now imported from prompt_loader.py
# which loads templates from the prompts/ folder

# ==========================================
# MASTER AUTOMATION CLASS
# ==========================================
class PeekrAutomationMaster:
    def __init__(self):
        """Initialize the complete automation system"""
        Config.validate_config()
        self.openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Set timezone from environment variable (configurable by client)
        try:
            self.timezone = pytz.timezone(Config.TIMEZONE)
            logger.info(f"TIMEZONE: Timezone set to: {Config.TIMEZONE} ({self.timezone})")
        except pytz.exceptions.UnknownTimeZoneError:
            logger.warning(f"WARNING: Unknown timezone '{Config.TIMEZONE}', falling back to UTC")
            self.timezone = pytz.UTC
            logger.info(f"TIMEZONE: Timezone set to: UTC (fallback)")
        
        # Test internet connectivity first
        if not test_internet_connectivity():
            logger.error("ERROR: No internet connectivity detected. Please check your connection.")
            raise ConnectionError("No internet connectivity")
        
        # Google Sheets connection with retry logic - using environment variables only
        def connect_to_sheets():
            self.gspread_client = get_google_sheets_client()
            if not self.gspread_client:
                raise Exception("Failed to create Google Sheets client from environment variables")
            self.sheet = self.gspread_client.open_by_key(Config.SPREADSHEET_ID)
            self.leads_worksheet = self.sheet.worksheet("Incoming Leads")
            logger.info("SUCCESS: Google Sheets connection established successfully")
        
        try:
            retry_with_backoff(
                connect_to_sheets,
                max_retries=3,
                exceptions=(ConnectionError, RequestException, NameResolutionError, socket.gaierror)
            )
        except Exception as e:
            logger.error(f"ERROR: Failed to connect to Google Sheets after multiple attempts: {e}")
            logger.error("TROUBLESHOOTING: Troubleshooting tips:")
            logger.error("   1. Check internet connectivity")
            logger.error("   2. Verify Google credentials file")
            logger.error("   3. Try flushing DNS cache: sudo dscacheutil -flushcache (macOS)")
            logger.error("   4. Check if googleapis.com is accessible")
            raise
        
        # Real-time email monitoring setup
        self.running = False
        self.email_queue = queue.Queue()
        self.valid_emails = set()
        self.processed_emails = set()
        self.existing_leads_cache = {}
        
        # Statistics
        self.stats = {
            'emails_processed': 0,
            'replies_sent': 0,
            'errors': 0,
            'start_time': datetime.now(self.timezone)
        }
        
        logger.info("READY: Peekr Automation Master initialized - ALL systems ready!")
    
    # ==========================================
    # 1. LEAD GENERATION (APIFY)
    # ==========================================
    def load_existing_leads_for_deduplication(self):
        """Load existing leads to prevent duplicates"""
        try:
            data = self.leads_worksheet.get_all_records()
            self.existing_leads_cache = {}
            
            for row in data:
                title = str(row.get('Title', '')).strip().lower()
                website = str(row.get('Website', '')).strip().lower()
                phone = str(row.get('Phone', '')).strip()
                
                if title:
                    title_hash = hashlib.md5(title.encode()).hexdigest()
                    self.existing_leads_cache[title_hash] = True
                
                if website:
                    website_hash = hashlib.md5(website.encode()).hexdigest()
                    self.existing_leads_cache[website_hash] = True
                
                if phone:
                    phone_hash = hashlib.md5(phone.encode()).hexdigest()
                    self.existing_leads_cache[phone_hash] = True
            
            logger.info(f"LOADED: Loaded {len(self.existing_leads_cache)} existing leads for deduplication")
            return True
            
        except Exception as e:
            logger.error(f"ERROR: Error loading existing leads: {e}")
            return False
    
    def is_duplicate_lead(self, lead_data):
        """Check if lead is duplicate using multiple criteria"""
        title = str(lead_data.get('title', '')).strip().lower()
        website = str(lead_data.get('website', '')).strip().lower()
        phone = str(lead_data.get('phone', '')).strip()
        
        # Create composite key and individual hashes
        composite_key = f"{title}|{website}|{phone}".replace(" ", "")
        title_hash = hashlib.md5(title.encode()).hexdigest()
        website_hash = hashlib.md5(website.encode()).hexdigest() if website else ""
        phone_hash = hashlib.md5(phone.encode()).hexdigest() if phone else ""
        
        # Check for duplicates
        if (composite_key in self.existing_leads_cache or 
            title_hash in self.existing_leads_cache or
            (website_hash and website_hash in self.existing_leads_cache) or
            (phone_hash and phone_hash in self.existing_leads_cache)):
            return True
        
        # Add to cache
        self.existing_leads_cache[composite_key] = True
        self.existing_leads_cache[title_hash] = True
        if website_hash: self.existing_leads_cache[website_hash] = True
        if phone_hash: self.existing_leads_cache[phone_hash] = True
        
        return False
    
    def search_leads_with_apify(self, location, category, max_results=75):
        """Search for leads using Apify (using your original working approach)"""
        try:
            # Using your original working API endpoint and approach
            url = "https://api.apify.com/v2/acts/lukaskrivka~google-maps-with-contact-details/run-sync-get-dataset-items"
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {Config.APIFY_API_KEY}'
            }
            
            payload = {
                "language": "en",
                "locationQuery": location,
                "maxCrawledPlacesPerSearch": max_results,
                "searchStringsArray": [f"{category} in {location}"],
                "skipClosedPlaces": False
            }
            
            logger.info(f"SEARCH: Searching Apify for '{category}' in '{location}' (max {max_results} results)")
            
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=600)
            
            logger.info(f"API: Apify response status: {response.status_code}")
            
            if response.status_code == 201:  # Your original used 201, not 200
                leads = response.json()
                logger.info(f"RESULT: Apify returned {len(leads)} raw leads for {category} in {location}")
                return leads
            else:
                logger.error(f"ERROR: Apify API error: {response.status_code}")
                logger.error(f"ERROR: Response content: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"ERROR: Error calling Apify API: {e}")
            return []
    
    def process_lead_data(self, raw_leads, category, location):
        """Process and filter lead data (matching your original approach)"""
        processed_leads = []
        
        for lead_data in raw_leads:
            if self.is_duplicate_lead(lead_data):
                continue
            
            # Extract and clean data (matching your original field names)
            title = str(lead_data.get('title', '')).strip()
            website = str(lead_data.get('website', '')).strip()
            
            # Handle emails array or single email (from your original code)
            emails_data = ""
            if lead_data.get('emails') and len(lead_data.get('emails', [])) > 0:
                # Clean and filter emails from the array
                email_list = [email.strip() for email in lead_data.get('emails', []) if email and email.strip()]
                emails_data = ", ".join(email_list)
            elif lead_data.get('email'):
                emails_data = str(lead_data.get('email', '')).strip()
            
            # Additional fallback - sometimes emails might be in other fields
            if not emails_data:
                # Check for other possible email fields
                for field in ['contactEmail', 'businessEmail', 'primaryEmail']:
                    if lead_data.get(field):
                        emails_data = str(lead_data.get(field, '')).strip()
                        break
            
            address = str(lead_data.get('address', '')).strip()
            
            # Handle phone numbers (useful as backup contact info)
            phone_data = ""
            if lead_data.get('phone'):
                phone_data = str(lead_data.get('phone', '')).strip()
            elif lead_data.get('phoneUnformatted'):
                phone_data = str(lead_data.get('phoneUnformatted', '')).strip()
            
            if not title or len(title) < 3:
                continue
            
            processed_lead = {
                'Title': title,
                'Website': website,
                'Email': emails_data,  # Emails from Apify (may contain multiple)
                'Valid Email': '',  # Will be filled by email validation step
                'Location': address or location,  # Use Apify address if available, else fallback
                'Category': category,
                'Status': 'Waiting',
                'Follow-up Count': 0,
                'Phone': phone_data  # Add phone for additional contact info
            }
            
            processed_leads.append(processed_lead)
        
        logger.info(f"SUCCESS: Processed {len(processed_leads)} unique leads")
        return processed_leads
    
    def save_leads_to_sheet(self, leads):
        """Save leads to Google Sheets"""
        try:
            if not leads:
                return 0
            
            # Get current data to append
            existing_data = self.leads_worksheet.get_all_values()
            start_row = len(existing_data) + 1
            
            # Prepare data for batch insert
            rows_to_insert = []
            for lead in leads:
                row = [
                    lead.get('Title', ''),
                    lead.get('Website', ''),
                    lead.get('Email', ''),
                    lead.get('Valid Email', ''),
                    lead.get('Location', ''),
                    '',  # domain
                    lead.get('Phone', ''),  # Phone number from Apify
                    lead.get('Category', ''),
                    '',  # Mail Send at
                    '',  # Mail Send time
                    '',  # Subject
                    lead.get('Status', 'Waiting'),
                    '',  # Mail Received
                    '',  # Reply Message
                    '',  # Mail reply send
                    '',  # Response
                    '',  # Follow Up
                    lead.get('Follow-up Count', 0),  # Follow-up Count
                    '',  # Last Follow-up Date
                    '',  # Follow-up Status
                    '',  # Reply Received
                    ''   # Reply Date
                ]
                rows_to_insert.append(row)
            
            # Batch insert
            if rows_to_insert:
                range_name = f"A{start_row}:V{start_row + len(rows_to_insert) - 1}"
                self.leads_worksheet.update(range_name, rows_to_insert)
                logger.info(f"SUCCESS: Saved {len(rows_to_insert)} leads to Google Sheets")
            
            return len(rows_to_insert)
            
        except Exception as e:
            logger.error(f"ERROR: Error saving leads to sheet: {e}")
            return 0
    
    def run_apify_lead_generation(self):
        """Main lead generation process"""
        try:
            logger.info("📊 Starting Apify lead generation...")
            
            # Load existing leads for deduplication
            if not self.load_existing_leads_for_deduplication():
                logger.error("ERROR:  Failed to load existing leads")
                return
            
            # Get categories and locations
            try:
                categories_sheet = self.sheet.worksheet("Categories")
                categories_data = categories_sheet.get_all_records()
                categories_df = pd.DataFrame(categories_data)
            except Exception as e:
                logger.error(f"ERROR:  Error loading categories: {e}")
                return
            
            if categories_df.empty:
                logger.error("ERROR:  No categories found")
                return
            
            total_leads_generated = 0
            target_leads = 300
            leads_per_search = 75
            
            logger.info(f"🎯 Target: {target_leads} leads with <10% duplication")
            
            # Process each category and location
            for index, row in categories_df.iterrows():
                if total_leads_generated >= target_leads:
                    break
                
                location = str(row.get('Location', '')).strip()
                category = str(row.get('Categories', '')).strip()
                
                if not location or not category:
                    continue
                
                # Search for leads
                raw_leads = self.search_leads_with_apify(location, category, leads_per_search)
                
                if raw_leads:
                    processed_leads = self.process_lead_data(raw_leads, category, location)
                    saved_count = self.save_leads_to_sheet(processed_leads)
                    total_leads_generated += saved_count
                    
                    logger.info(f"📈 Progress: {total_leads_generated}/{target_leads} leads")
                    time.sleep(10)  # Rate limiting
            
            logger.info(f"🎉 Lead generation completed! Generated {total_leads_generated} new leads")
            
        except Exception as e:
            logger.error(f"ERROR:  Lead generation failed: {e}")
    
    # ==========================================
    # 2. EMAIL OUTREACH
    # ==========================================
    def is_valid_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def is_business_email(self, email):
        """Check if email is a valid business email (not generic)"""
        if not email or not self.is_valid_email(email):
            return False
        
        email_lower = email.lower()
        
        # Exclude generic/non-business email patterns
        excluded_patterns = [
            'hr@', 'support@', 'info@', 'admin@', 'noreply@', 'no-reply@',
            'contact@', 'sales@', 'marketing@', 'help@', 'service@',
            'office@', 'reception@', 'general@', 'customer@', 'team@',
            'mail@', 'enquiry@', 'inquiry@', 'hello@', 'web@'
        ]
        
        # Check if email starts with excluded patterns
        for pattern in excluded_patterns:
            if email_lower.startswith(pattern):
                return False
        
        # Additional checks for generic terms in email
        excluded_terms = [
            'noreply', 'no-reply', 'donotreply', 'do-not-reply',
            'postmaster', 'mailer-daemon', 'bounce'
        ]
        
        email_prefix = email_lower.split('@')[0]
        for term in excluded_terms:
            if term in email_prefix:
                return False
        
        return True
    
    def extract_best_email(self, email_data):
        """Extract the best business email from email data"""
        if not email_data:
            return None
        
        # Handle multiple emails (comma or semicolon separated)
        if ',' in email_data or ';' in email_data:
            emails = re.split('[,;]', email_data)
        else:
            emails = [email_data]
        
        # Clean and validate each email
        valid_emails = []
        for email in emails:
            email = email.strip()
            if self.is_business_email(email):
                valid_emails.append(email)
        
        if not valid_emails:
            return None
        
        # Prefer emails that look like decision-maker emails
        preferred_patterns = [
            r'^[a-zA-Z]+\.[a-zA-Z]+@',  # firstname.lastname@
            r'^[a-zA-Z]{2,}@',          # reasonable length names
            r'^(ceo|cto|cfo|founder|owner|director|manager)[@\.]'  # executive titles
        ]
        
        # First, try to find preferred emails
        for pattern in preferred_patterns:
            for email in valid_emails:
                if re.match(pattern, email.lower()):
                    return email
        
        # If no preferred email found, return the first valid one
        return valid_emails[0]
    
    def generate_subject_and_body(self, title, category):
        """Generate email subject and body using AI"""
        try:
            prompt = get_subject_prompt(title, category)
            
            response = self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional B2B email writer. Generate compelling email content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse response - JSON format from external prompts
            subject = ""
            body = ""
            solutions = ["Optimize workflows", "Improve efficiency", "Drive growth"]
            
            # Debug the AI response
            logger.debug(f"🤖 AI Response:\n{content}")
            
            try:
                # Try to parse as JSON (new format from external prompts)
                import json
                
                # Extract JSON from response (may be wrapped in markdown)
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_content = content[json_start:json_end]
                    data = json.loads(json_content)
                    
                    subject = data.get('subject', '')
                    body = data.get('email', '')
                    solutions = data.get('solutions', solutions)
                    
                    logger.debug(f"SUCCESS: JSON parsing successful")
                else:
                    raise ValueError("No JSON found in response")
                    
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.debug(f"ERROR:  JSON parsing failed: {e}, trying fallback parsing...")
                
                # Fallback to old format parsing
                lines = content.split('\n')
                current_section = None
                body_lines = []
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('SUBJECT:'):
                        subject = line.replace('SUBJECT:', '').strip()
                        current_section = "subject"
                    elif line.startswith('BODY:'):
                        body_content = line.replace('BODY:', '').strip()
                        if body_content:
                            body_lines.append(body_content)
                        current_section = "body"
                    elif line.startswith('SOLUTIONS:'):
                        solutions_text = line.replace('SOLUTIONS:', '').strip()
                        if '|' in solutions_text:
                            solutions = [s.strip() for s in solutions_text.split('|')]
                        current_section = "solutions"
                    elif current_section == "body" and line:
                        body_lines.append(line)
                
                # Join body lines
                body = ' '.join(body_lines) if body_lines else ""
                
                # Final fallback if both parsing methods failed
                if not body and content:
                    if "Dear" in content or "Hello" in content or "<p>" in content:
                        body = content
                        if not subject:
                            first_line = content.split('\n')[0]
                            if len(first_line) < 100:
                                subject = first_line.strip()
                                body = '\n'.join(content.split('\n')[1:]).strip()
            
            logger.debug(f"📧 Parsed - Subject: '{subject[:50]}...', Body length: {len(body)}")
            
            return subject, body, solutions
            
        except Exception as e:
            logger.error(f"ERROR:  Error generating email content: {e}")
            return "", "", ["Optimize workflows", "Improve efficiency", "Drive growth"]
    
    def send_email(self, to_email, subject, html_body):
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart()
            msg["From"] = f"{Config.SENDER_NAME} <{Config.EMAIL_ACCOUNT}>"
            msg["To"] = to_email
            msg["Subject"] = f"{subject} - Let's Explore"
            msg.attach(MIMEText(html_body, "html"))
            
            with smtplib.SMTP_SSL(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
                server.login(Config.EMAIL_ACCOUNT, Config.EMAIL_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"SUCCESS: Email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"ERROR:  Failed to send email to {to_email}: {e}")
            return False
    
    def run_email_outreach(self):
        """Main email outreach process"""
        try:
            logger.info("📧 Starting email outreach campaign...")
            
            data = self.leads_worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            # Step 1: Email Validation and Filtering
            logger.info("🔍 Step 1: Filtering and validating emails...")
            validation_count = 0
            
            for index, row in df.iterrows():
                email_data = row.get("Email", "")
                valid_email = row.get("Valid Email", "")
                status = str(row.get("Status", "")).strip().upper()
                
                # Skip if already has valid email or not waiting
                if valid_email or status != "WAITING" or not email_data:
                    continue
                
                # Extract best business email
                best_email = self.extract_best_email(email_data)
                
                if best_email:
                    row_number = index + 2
                    try:
                        # Update Valid Email column
                        self.leads_worksheet.update_cell(row_number, 4, best_email)  # Column D (Valid Email)
                        logger.info(f"SUCCESS: Validated email for row {row_number}: {best_email}")
                        validation_count += 1
                        time.sleep(1)  # Rate limiting for sheet updates
                    except Exception as e:
                        logger.error(f"ERROR:  Error updating Valid Email for row {row_number}: {e}")
                else:
                    logger.debug(f"WARNING: No valid business email found in: {email_data}")
            
            logger.info(f"📊 Email validation completed: {validation_count} emails validated")
            
            # Step 2: Reload data to get updated Valid Email column
            logger.info("🔄 Step 2: Reloading data with validated emails...")
            data = self.leads_worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            # Step 3: Send emails to validated addresses
            logger.info("📧 Step 3: Sending outreach emails...")
            sent_count = 0
            
            for index, row in df.iterrows():
                valid_email = row.get("Valid Email", "").strip()
                title = row.get("Title", "")
                category = row.get("Category", "")
                status = str(row.get("Status", "")).strip().upper()
                
                # Only send to rows with valid email and waiting status
                if not valid_email or status != "WAITING":
                    continue
                
                row_number = index + 2
                
                try:
                    # Generate content
                    subject, body, solutions = self.generate_subject_and_body(title, category)
                    
                    if not subject or not body:
                        logger.warning(f"WARNING: Failed to generate content for {title}")
                        continue
                    
                    # Load email template
                    try:
                        with open(Config.EMAIL_TEMPLATE_PATH, "r", encoding="utf-8") as file:
                            html_template = file.read()
                    except FileNotFoundError:
                        # Fallback simple template
                        html_template = """
                        <html><body>
                        <h2>{{Subject}}</h2>
                        <p>Dear {{Title}},</p>
                        <div>{{body}}</div>
                        <ul>
                        <li>{{solution1}}</li>
                        <li>{{solution2}}</li>
                        <li>{{solution3}}</li>
                        </ul>
                        <p>Best regards,<br>Muhammad from Peekr</p>
                        </body></html>
                        """
                    
                    # Replace template variables
                    html_body = html_template.replace("{{Subject}}", subject)
                    html_body = html_body.replace("{{Title}}", title)
                    html_body = html_body.replace("{{body}}", body)
                    html_body = html_body.replace("{{solution1}}", solutions[0] if len(solutions) > 0 else "Optimize workflows")
                    html_body = html_body.replace("{{solution2}}", solutions[1] if len(solutions) > 1 else "Improve efficiency")
                    html_body = html_body.replace("{{solution3}}", solutions[2] if len(solutions) > 2 else "Drive growth")
                    
                    # Send email to validated address
                    success = self.send_email(valid_email, subject, html_body)
                    
                    if success:
                        # Update sheet with sent status and metadata
                        self.leads_worksheet.update_cell(row_number, 12, "Sent")  # Status (Column L)
                        self.leads_worksheet.update_cell(row_number, 11, subject)  # Subject (Column K)
                        
                        current_time = datetime.now(self.timezone)
                        self.leads_worksheet.update_cell(row_number, 9, current_time.strftime("%Y-%m-%d"))  # Mail Send at (Column I)
                        self.leads_worksheet.update_cell(row_number, 10, current_time.strftime("%H:%M:%S"))  # Mail Send time (Column J)
                        
                        logger.info(f"📧 Email sent to {valid_email} ({title})")
                        sent_count += 1
                        time.sleep(10)  # Rate limiting between emails
                    else:
                        logger.error(f"ERROR:  Failed to send email to {valid_email}")
                
                except Exception as e:
                    logger.error(f"ERROR:  Error processing {valid_email}: {e}")
            
            logger.info(f"SUCCESS: Email outreach completed! Sent {sent_count} emails")
            
        except Exception as e:
            logger.error(f"ERROR:  Email outreach failed: {e}")
    
    # ==========================================
    # 3. REAL-TIME REPLY MONITORING
    # ==========================================
    def load_valid_emails(self):
        """Load valid emails for monitoring"""
        try:
            data = self.leads_worksheet.get_all_records()
            emails = {row.get('Valid Email', '').strip().lower() for row in data if row.get('Valid Email')}
            self.valid_emails = {email for email in emails if email and '@' in email}
            
            logger.info(f"📋 Loaded {len(self.valid_emails)} valid emails for monitoring")
            return True
            
        except Exception as e:
            logger.error(f"ERROR:  Error loading valid emails: {e}")
            return False
    
    def check_new_emails_fast(self):
        """Check for new emails quickly"""
        try:
            # Test DNS resolution first
            try:
                socket.gethostbyname(Config.IMAP_SERVER)
            except socket.gaierror:
                return 0  # Skip this check if DNS resolution fails
            
            mail = imaplib.IMAP4_SSL(Config.IMAP_SERVER, Config.IMAP_PORT)
            mail.login(Config.EMAIL_ACCOUNT, Config.EMAIL_PASSWORD)
            mail.select("inbox")
            
            # Search for unseen emails
            result, data = mail.search(None, '(UNSEEN)')
            mail_ids = data[0].split()
            
            new_emails = 0
            for mail_id in mail_ids:
                # Get email headers quickly
                result, msg_data = mail.fetch(mail_id, '(BODY[HEADER.FIELDS (FROM SUBJECT)])')
                
                if result == 'OK' and msg_data[0]:
                    header_data = msg_data[0][1].decode()
                    
                    # Extract sender
                    from_match = re.search(r'From: (.+)', header_data)
                    if from_match:
                        from_line = from_match.group(1)
                        from_email = re.findall(r'[\w\.-]+@[\w\.-]+', from_line)
                        
                        if from_email and from_email[0].lower() in self.valid_emails:
                            # Extract subject
                            subject_match = re.search(r'Subject: (.+)', header_data)
                            subject = subject_match.group(1) if subject_match else "No Subject"
                            
                            # Add to processing queue
                            email_info = {
                                'id': mail_id,
                                'sender': from_email[0].lower(),
                                'subject': subject.strip()
                            }
                            
                            self.email_queue.put(email_info)
                            new_emails += 1
            
            mail.close()
            mail.logout()
            
            if new_emails > 0:
                logger.info(f"📧 Found {new_emails} new emails to process")
            
            return new_emails
            
        except Exception as e:
            logger.error(f"ERROR:  Error checking emails: {e}")
            return 0
    
    def extract_email_body(self, msg):
        """Extract text from email"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode(errors='ignore')
                        break
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode(errors='ignore')
        
        return body.strip()
    
    def classify_interest(self, email_body):
        """Classify email interest level using AI"""
        try:
            prompt = classify(email_body)
            
            response = self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an AI that classifies email interest levels. Respond with EXACTLY 'INTERESTED' or 'NOT INTERESTED'."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            classification = response.choices[0].message.content.strip().upper()
            return "INTERESTED" if "INTERESTED" in classification else "NOT INTERESTED"
            
        except Exception as e:
            logger.error(f"ERROR:  Error classifying interest: {e}")
            return "NOT INTERESTED"
    
    def send_reply(self, to_email, original_subject, email_content, interest_level):
        """Send personalized reply"""
        try:
            if interest_level == "INTERESTED":
                prompt = generate_interested_reply(email_content)
            else:
                prompt = generate_not_interested_reply(email_content)
            
            response = self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional B2B email writer. Generate personalized replies in HTML format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            reply_content = response.choices[0].message.content.strip()
            
            # Send email
            subject = f"Re: {original_subject}" if original_subject else "Thank you for your response"
            
            msg = MIMEMultipart()
            msg["From"] = f"{Config.SENDER_NAME} <{Config.EMAIL_ACCOUNT}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(reply_content, "html"))
            
            with smtplib.SMTP_SSL(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
                server.login(Config.EMAIL_ACCOUNT, Config.EMAIL_PASSWORD)
                server.sendmail(Config.EMAIL_ACCOUNT, to_email, msg.as_string())
            
            logger.info(f"SUCCESS: {interest_level} reply sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"ERROR:  Error sending reply to {to_email}: {e}")
            return False
    
    def update_lead_status(self, email, status, reply_content=""):
        """Update lead status in Google Sheets"""
        try:
            data = self.leads_worksheet.get_all_records()
            for i, row in enumerate(data, start=2):
                if row.get('Valid Email', '').strip().lower() == email.lower():
                    current_date = datetime.now(self.timezone).strftime('%Y-%m-%d')
                    
                    # Update reply tracking
                    self.leads_worksheet.update_cell(i, 13, "YES")  # Mail Received (Column M)
                    self.leads_worksheet.update_cell(i, 14, reply_content[:500])  # Reply Message (Column N)
                    self.leads_worksheet.update_cell(i, 15, "YES")  # Mail reply send (Column O)
                    self.leads_worksheet.update_cell(i, 21, status)  # Reply Received (Column U)
                    self.leads_worksheet.update_cell(i, 22, current_date)  # Reply Date (Column V)
                    
                    break
                    
        except Exception as e:
            logger.error(f"ERROR:  Error updating lead status: {e}")
    
    def process_email_detailed(self, email_info):
        """Process email in detail"""
        try:
            mail = imaplib.IMAP4_SSL(Config.IMAP_SERVER, Config.IMAP_PORT)
            mail.login(Config.EMAIL_ACCOUNT, Config.EMAIL_PASSWORD)
            mail.select("inbox")
            
            # Get full email content
            result, msg_data = mail.fetch(email_info['id'], "(RFC822)")
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Get email body
                    email_body = self.extract_email_body(msg)
                    
                    if not email_body.strip():
                        continue
                    
                    logger.info(f"📧 Processing reply from: {email_info['sender']}")
                    
                    # Classify interest level
                    interest_level = self.classify_interest(email_body)
                    logger.info(f"🎯 Interest level: {interest_level}")
                    
                    # Send appropriate reply
                    reply_sent = self.send_reply(
                        email_info['sender'], 
                        email_info['subject'], 
                        email_body, 
                        interest_level
                    )
                    
                    # Update statistics
                    self.stats['emails_processed'] += 1
                    if reply_sent:
                        self.stats['replies_sent'] += 1
                        # Update Google Sheet
                        self.update_lead_status(email_info['sender'], interest_level, email_body)
                    
                    # Mark email as read
                    mail.store(email_info['id'], '+FLAGS', '\\Seen')
                    
                    break
            
            mail.close()
            mail.logout()
            return True
            
        except Exception as e:
            logger.error(f"ERROR:  Error processing email from {email_info['sender']}: {e}")
            self.stats['errors'] += 1
            return False
    
    def email_processor_worker(self):
        """Worker thread for processing emails"""
        while self.running:
            try:
                email_info = self.email_queue.get(timeout=5)
                success = self.process_email_detailed(email_info)
                self.email_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"ERROR:  Error in email processor worker: {e}")
    
    def start_realtime_reply_monitoring(self):
        """Start real-time reply monitoring"""
        logger.info("📡 Starting REAL-TIME email reply monitoring...")
        
        if not self.load_valid_emails():
            logger.error("ERROR:  Failed to load valid emails")
            return
        
        self.running = True
        
        # Start worker threads
        num_workers = min(5, max(2, len(self.valid_emails) // 50))
        for i in range(num_workers):
            worker = threading.Thread(target=self.email_processor_worker, daemon=True)
            worker.start()
        
        logger.info(f"🔧 Started {num_workers} email processor workers")
        
        # Main monitoring loop
        check_interval = 5
        last_stats_report = datetime.now(self.timezone)
        consecutive_errors = 0
        last_error_log = datetime.now(self.timezone) - timedelta(minutes=10)
        
        def monitoring_loop():
            nonlocal last_stats_report, consecutive_errors, last_error_log
            
            while self.running:
                try:
                    new_emails = self.check_new_emails_fast()
                    consecutive_errors = 0  # Reset error counter on success
                    
                    # Report statistics every 5 minutes
                    if datetime.now(self.timezone) - last_stats_report > timedelta(minutes=5):
                        uptime = datetime.now(self.timezone) - self.stats['start_time']
                        logger.info("="*50)
                        logger.info("📊 REAL-TIME EMAIL MONITORING STATS")
                        logger.info(f"⏰ Uptime: {uptime}")
                        logger.info(f"📧 Emails processed: {self.stats['emails_processed']}")
                        logger.info(f"✉️ Replies sent: {self.stats['replies_sent']}")
                        logger.info(f"ERROR:  Network errors: {consecutive_errors}")
                        logger.info(f"📦 Queue size: {self.email_queue.qsize()}")
                        logger.info("="*50)
                        last_stats_report = datetime.now(self.timezone)
                        
                        # Reload valid emails
                        self.load_valid_emails()
                    
                    time.sleep(check_interval)
                    
                except Exception as e:
                    consecutive_errors += 1
                    # Only log errors every 5 minutes to avoid spam
                    if datetime.now(self.timezone) - last_error_log > timedelta(minutes=5):
                        logger.warning(f"WARNING: Network connectivity issues detected (errors: {consecutive_errors})")
                        logger.info("🔧 Email monitoring will continue when connectivity is restored")
                        last_error_log = datetime.now(self.timezone)
                    
                    # Longer sleep when there are connectivity issues
                    sleep_time = min(60, 10 + consecutive_errors * 2)
                    time.sleep(sleep_time)
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitor_thread.start()
        
        logger.info("SUCCESS: Real-time reply monitoring started successfully")
    
    # ==========================================
    # 4. FOLLOW-UP CAMPAIGNS
    # ==========================================
    def get_follow_up_candidates(self):
        """Get candidates who need follow-up emails"""
        try:
            data = self.leads_worksheet.get_all_records()
            candidates = []
            current_date = datetime.now(self.timezone)
            
            for i, row in enumerate(data, start=2):
                email = row.get('Valid Email', '').strip().lower()
                status = row.get('Status', '').strip()
                mail_received = row.get('Mail Received', '').strip()
                reply_message = row.get('Reply Message', '').strip()
                followup_count = int(row.get('Follow-up Count', 0) or 0)
                last_followup_date = row.get('Last Follow-up Date', '').strip()
                reply_received = row.get('Reply Received', '').strip()
                
                # Skip if no email or already sent 3 follow-ups
                if not email or followup_count >= 3:
                    continue
                
                needs_followup = False
                followup_type = None
                
                # Case 1: No response (non-responder)
                if not reply_message and (status == 'Sent' and mail_received != 'YES'):
                    if followup_count == 0:
                        sent_date_str = row.get('Mail Send at', '')
                        if sent_date_str:
                            try:
                                sent_date = datetime.strptime(sent_date_str, '%Y-%m-%d')
                                if current_date >= sent_date + timedelta(days=7):
                                    needs_followup = True
                                    followup_type = 'NON_RESPONDER'
                            except ValueError:
                                pass
                    elif followup_count > 0 and last_followup_date:
                        try:
                            last_date = datetime.strptime(last_followup_date, '%Y-%m-%d')
                            if current_date >= last_date + timedelta(days=7):
                                needs_followup = True
                                followup_type = 'NON_RESPONDER'
                        except ValueError:
                            pass
                
                # Case 2: Replied "NOT INTERESTED"
                elif reply_received and 'NOT INTERESTED' in reply_received.upper():
                    if followup_count == 0:
                        reply_date_str = row.get('Reply Date', '')
                        if reply_date_str:
                            try:
                                reply_date = datetime.strptime(reply_date_str, '%Y-%m-%d')
                                if current_date >= reply_date + timedelta(days=14):
                                    needs_followup = True
                                    followup_type = 'NOT_INTERESTED'
                            except ValueError:
                                pass
                    elif followup_count > 0 and last_followup_date:
                        try:
                            last_date = datetime.strptime(last_followup_date, '%Y-%m-%d')
                            if current_date >= last_date + timedelta(days=14):
                                needs_followup = True
                                followup_type = 'NOT_INTERESTED'
                        except ValueError:
                            pass
                
                if needs_followup:
                    candidates.append({
                        'row_index': i,
                        'email': email,
                        'title': row.get('Title', ''),
                        'category': row.get('Category', ''),
                        'website': row.get('Website', ''),
                        'followup_count': followup_count,
                        'followup_type': followup_type
                    })
            
            logger.info(f"📋 Found {len(candidates)} candidates for follow-up")
            return candidates
            
        except Exception as e:
            logger.error(f"ERROR:  Error getting follow-up candidates: {e}")
            return []
    
    def send_followup_email(self, candidate):
        """Send follow-up email"""
        try:
            if candidate['followup_type'] == 'NON_RESPONDER':
                prompt = generate_followup_prompt(
                    candidate['title'], 
                    candidate['category'], 
                    candidate['website']
                )
                subject = f"Following up - {candidate['title']}"
            else:  # NOT_INTERESTED
                prompt = generate_not_interested_reply(
                    f"Previous response: Not interested. Follow-up #{candidate['followup_count'] + 1}"
                )
                subject = f"Re: Following up - {candidate['title']}"
            
            response = self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional B2B email writer. Generate follow-up emails in HTML format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            email_content = response.choices[0].message.content.strip()
            
            # Send email
            msg = MIMEMultipart()
            msg["From"] = f"{Config.SENDER_NAME} <{Config.EMAIL_ACCOUNT}>"
            msg["To"] = candidate['email']
            msg["Subject"] = subject
            msg.attach(MIMEText(email_content, "html"))
            
            with smtplib.SMTP_SSL(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
                server.login(Config.EMAIL_ACCOUNT, Config.EMAIL_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"SUCCESS: Follow-up #{candidate['followup_count'] + 1} sent to {candidate['email']}")
            return True
            
        except Exception as e:
            logger.error(f"ERROR:  Error sending follow-up to {candidate['email']}: {e}")
            return False
    
    def update_followup_tracking(self, candidate, success):
        """Update follow-up tracking in Google Sheets"""
        try:
            if success:
                row_index = candidate['row_index']
                new_count = candidate['followup_count'] + 1
                current_date = datetime.now(self.timezone).strftime('%Y-%m-%d')
                
                # Update tracking columns
                self.leads_worksheet.update_cell(row_index, 18, new_count)  # Follow-up Count (Column R)
                self.leads_worksheet.update_cell(row_index, 19, current_date)  # Last Follow-up Date (Column S)
                
                # Update status
                if new_count >= 3:
                    status = f"Follow-up Complete (3/3) SUCCESS:"
                else:
                    status = f"Follow-up Sent ({new_count}/3) 📧"
                
                self.leads_worksheet.update_cell(row_index, 20, status)  # Follow-up Status (Column T)
                
                logger.info(f"📊 Updated tracking for {candidate['email']}: {new_count}/3")
            
        except Exception as e:
            logger.error(f"ERROR:  Error updating tracking: {e}")
    
    def run_followup_campaign(self):
        """Main follow-up campaign process"""
        try:
            logger.info("🔄 Starting AUTOMATED follow-up campaign...")
            
            candidates = self.get_follow_up_candidates()
            
            if not candidates:
                logger.info("SUCCESS: No follow-ups needed at this time")
                return
            
            sent_count = 0
            for candidate in candidates:
                success = self.send_followup_email(candidate)
                self.update_followup_tracking(candidate, success)
                
                if success:
                    sent_count += 1
                
                time.sleep(2)  # Rate limiting
            
            logger.info(f"🎉 Follow-up campaign completed! Sent {sent_count}/{len(candidates)} emails")
            
        except Exception as e:
            logger.error(f"ERROR:  Follow-up campaign failed: {e}")
    
    # ==========================================
    # 5. MASTER SCHEDULER
    # ==========================================
    def setup_schedules(self):
        """Setup all automated schedules in configured timezone"""
        timezone_name = Config.TIMEZONE
        logger.info(f"📅 Setting up ALL automated schedules in {timezone_name}...")
        
        # Lead generation: Sunday & Wednesday at midnight
        schedule.every().sunday.at("00:00").do(self.run_apify_lead_generation)
        schedule.every().wednesday.at("00:00").do(self.run_apify_lead_generation)
        logger.info(f"📊 Scheduled: Lead generation - Sunday & Wednesday at midnight {timezone_name}")
        
        # Email outreach: Tuesday & Thursday at 8 AM
        schedule.every().tuesday.at("08:00").do(self.run_email_outreach)
        schedule.every().thursday.at("08:00").do(self.run_email_outreach)
        logger.info(f"📧 Scheduled: Email outreach - Tuesday & Thursday at 11 AM {timezone_name}")
        
        # Follow-up campaigns: Monday at 11 AM
        schedule.every().monday.at("08:00").do(self.run_followup_campaign)
        logger.info(f"🔄 Scheduled: Follow-up campaigns - Monday at 11 AM {timezone_name}")
        
        # Start real-time reply monitoring immediately
        self.start_realtime_reply_monitoring()
        logger.info(f"📡 Started: REAL-TIME reply monitoring - 24/7 {timezone_name}")
    
    def run_master_automation(self):
        """Run the complete automation system"""
        logger.info("🚀 PEEKR AUTOMATION MASTER - Starting ALL systems...")
        logger.info("=" * 60)
        logger.info("🎯 This ONE file handles EVERYTHING:")
        logger.info("   📊 Lead Generation (Apify)")
        logger.info("   📧 Email Outreach")
        logger.info("   📡 Real-time Reply Monitoring")
        logger.info("   🔄 Follow-up Campaigns")
        logger.info("=" * 60)
        
        # Setup all schedules
        self.setup_schedules()
        
        logger.info("SUCCESS: All systems operational! Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("🛑 Stopping all automation systems...")
            self.running = False
            logger.info("👋 Peekr Automation Master stopped.")
        except Exception as e:
            logger.error(f"ERROR:  Master automation error: {e}")

# ==========================================
# MAIN ENTRY POINT
# ==========================================
def main():
    """Single entry point for ALL automation"""
    Config.validate_config()
    
    automation = PeekrAutomationMaster()
    automation.run_master_automation()

if __name__ == "__main__":
    main() 