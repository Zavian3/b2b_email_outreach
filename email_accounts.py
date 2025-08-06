#!/usr/bin/env python3
"""
Email Accounts Management System
===============================

Manages multiple email accounts for B2B outreach campaigns.
Stores account configurations and handles account selection.
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from credentials_helper import get_google_sheets_client

logger = logging.getLogger(__name__)

@dataclass
class EmailAccount:
    """Email account configuration"""
    id: str
    name: str
    email: str
    password: str
    smtp_server: str
    smtp_port: int
    imap_server: str
    imap_port: int
    sender_name: str
    is_active: bool = False
    created_at: str = None
    last_used: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailAccount':
        """Create from dictionary"""
        return cls(**data)
    
    def validate(self) -> List[str]:
        """Validate email account configuration"""
        errors = []
        
        if not self.name.strip():
            errors.append("Account name is required")
        
        if not self.email.strip() or '@' not in self.email:
            errors.append("Valid email address is required")
        
        if not self.password.strip():
            errors.append("Password is required")
        
        if not self.smtp_server.strip():
            errors.append("SMTP server is required")
        
        if not isinstance(self.smtp_port, int) or self.smtp_port <= 0:
            errors.append("Valid SMTP port is required")
        
        if not self.imap_server.strip():
            errors.append("IMAP server is required")
        
        if not isinstance(self.imap_port, int) or self.imap_port <= 0:
            errors.append("Valid IMAP port is required")
        
        if not self.sender_name.strip():
            errors.append("Sender name is required")
        
        return errors


class EmailAccountManager:
    """Manages email accounts storage and operations"""
    
    def __init__(self, spreadsheet_id: str):
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = "Email_Accounts"
        self._accounts_cache: Dict[str, EmailAccount] = {}
        self._cache_timestamp = None
        self._cache_duration = 300  # 5 minutes
    
    def _get_sheet(self):
        """Get or create the Email_Accounts sheet"""
        try:
            client = get_google_sheets_client()
            spreadsheet = client.open_by_key(self.spreadsheet_id)
            
            try:
                sheet = spreadsheet.worksheet(self.sheet_name)
            except Exception:
                # Create the sheet if it doesn't exist
                sheet = spreadsheet.add_worksheet(
                    title=self.sheet_name,
                    rows=100,
                    cols=15
                )
                
                # Add headers
                headers = [
                    'ID', 'Name', 'Email', 'Password', 'SMTP_Server', 'SMTP_Port',
                    'IMAP_Server', 'IMAP_Port', 'Sender_Name', 'Is_Active',
                    'Created_At', 'Last_Used'
                ]
                sheet.append_row(headers)
                logger.info(f"✅ Created new {self.sheet_name} sheet")
            
            return sheet
            
        except Exception as e:
            logger.error(f"❌ Error accessing {self.sheet_name} sheet: {e}")
            raise
    
    def _should_refresh_cache(self) -> bool:
        """Check if cache should be refreshed"""
        if not self._cache_timestamp:
            return True
        
        age = datetime.now().timestamp() - self._cache_timestamp
        return age > self._cache_duration
    
    def _refresh_cache(self):
        """Refresh accounts cache from Google Sheets"""
        try:
            sheet = self._get_sheet()
            records = sheet.get_all_records()
            
            self._accounts_cache = {}
            for record in records:
                if record.get('ID'):  # Skip empty rows
                    account = EmailAccount(
                        id=record['ID'],
                        name=record['Name'],
                        email=record['Email'],
                        password=record['Password'],
                        smtp_server=record['SMTP_Server'],
                        smtp_port=int(record['SMTP_Port']) if record['SMTP_Port'] else 465,
                        imap_server=record['IMAP_Server'],
                        imap_port=int(record['IMAP_Port']) if record['IMAP_Port'] else 993,
                        sender_name=record['Sender_Name'],
                        is_active=str(record.get('Is_Active', 'False')).lower() == 'true',
                        created_at=record.get('Created_At'),
                        last_used=record.get('Last_Used')
                    )
                    self._accounts_cache[account.id] = account
            
            self._cache_timestamp = datetime.now().timestamp()
            logger.info(f"📊 Refreshed email accounts cache: {len(self._accounts_cache)} accounts")
            
        except Exception as e:
            logger.error(f"❌ Error refreshing accounts cache: {e}")
            raise
    
    def get_all_accounts(self) -> List[EmailAccount]:
        """Get all email accounts"""
        if self._should_refresh_cache():
            self._refresh_cache()
        
        return list(self._accounts_cache.values())
    
    def get_account(self, account_id: str) -> Optional[EmailAccount]:
        """Get specific email account"""
        if self._should_refresh_cache():
            self._refresh_cache()
        
        return self._accounts_cache.get(account_id)
    
    def get_active_account(self) -> Optional[EmailAccount]:
        """Get the currently active email account"""
        accounts = self.get_all_accounts()
        active_accounts = [acc for acc in accounts if acc.is_active]
        
        if not active_accounts:
            return None
        
        if len(active_accounts) > 1:
            logger.warning(f"⚠️ Multiple active accounts found, using first one")
        
        return active_accounts[0]
    
    def add_account(self, account: EmailAccount) -> bool:
        """Add new email account"""
        try:
            # Validate account
            errors = account.validate()
            if errors:
                raise ValueError(f"Account validation failed: {', '.join(errors)}")
            
            # Check for duplicate email
            existing_accounts = self.get_all_accounts()
            if any(acc.email.lower() == account.email.lower() for acc in existing_accounts):
                raise ValueError(f"Account with email {account.email} already exists")
            
            # Add to sheet
            sheet = self._get_sheet()
            row_data = [
                account.id, account.name, account.email, account.password,
                account.smtp_server, account.smtp_port, account.imap_server,
                account.imap_port, account.sender_name, account.is_active,
                account.created_at, account.last_used or ""
            ]
            sheet.append_row(row_data)
            
            # Update cache
            self._accounts_cache[account.id] = account
            
            logger.info(f"✅ Added email account: {account.name} ({account.email})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding email account: {e}")
            raise
    
    def update_account(self, account: EmailAccount) -> bool:
        """Update existing email account"""
        try:
            # Validate account
            errors = account.validate()
            if errors:
                raise ValueError(f"Account validation failed: {', '.join(errors)}")
            
            sheet = self._get_sheet()
            records = sheet.get_all_records()
            
            # Find the row to update
            row_index = None
            for i, record in enumerate(records, start=2):  # Start from row 2 (after header)
                if record['ID'] == account.id:
                    row_index = i
                    break
            
            if row_index is None:
                raise ValueError(f"Account with ID {account.id} not found")
            
            # Update the row
            row_data = [
                account.id, account.name, account.email, account.password,
                account.smtp_server, account.smtp_port, account.imap_server,
                account.imap_port, account.sender_name, account.is_active,
                account.created_at, account.last_used or ""
            ]
            
            for col, value in enumerate(row_data, start=1):
                sheet.update_cell(row_index, col, value)
            
            # Update cache
            self._accounts_cache[account.id] = account
            
            logger.info(f"✅ Updated email account: {account.name} ({account.email})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating email account: {e}")
            raise
    
    def delete_account(self, account_id: str) -> bool:
        """Delete email account"""
        try:
            sheet = self._get_sheet()
            records = sheet.get_all_records()
            
            # Find the row to delete
            row_index = None
            for i, record in enumerate(records, start=2):  # Start from row 2 (after header)
                if record['ID'] == account_id:
                    row_index = i
                    break
            
            if row_index is None:
                raise ValueError(f"Account with ID {account_id} not found")
            
            # Delete the row
            sheet.delete_rows(row_index)
            
            # Remove from cache
            if account_id in self._accounts_cache:
                del self._accounts_cache[account_id]
            
            logger.info(f"✅ Deleted email account: {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting email account: {e}")
            raise
    
    def set_active_account(self, account_id: str) -> bool:
        """Set account as active (deactivating all others)"""
        try:
            accounts = self.get_all_accounts()
            
            # Deactivate all accounts first
            for account in accounts:
                account.is_active = False
                self.update_account(account)
            
            # Activate the selected account
            target_account = self.get_account(account_id)
            if not target_account:
                raise ValueError(f"Account with ID {account_id} not found")
            
            target_account.is_active = True
            target_account.last_used = datetime.now().isoformat()
            self.update_account(target_account)
            
            logger.info(f"✅ Set active email account: {target_account.name} ({target_account.email})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting active account: {e}")
            raise
    
    def create_default_account_from_env(self) -> bool:
        """Create default account from environment variables if no accounts exist"""
        try:
            accounts = self.get_all_accounts()
            if accounts:
                return False  # Accounts already exist
            
            # Get env values
            email_account = os.getenv('EMAIL_ACCOUNT')
            email_password = os.getenv('EMAIL_PASSWORD')
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', 465))
            imap_server = os.getenv('IMAP_SERVER')
            imap_port = int(os.getenv('IMAP_PORT', 993))
            sender_name = os.getenv('SENDER_NAME')
            
            if not all([email_account, email_password, smtp_server, imap_server, sender_name]):
                return False  # Missing required env vars
            
            # Create default account
            account = EmailAccount(
                id="default",
                name="Default Account (from ENV)",
                email=email_account,
                password=email_password,
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                imap_server=imap_server,
                imap_port=imap_port,
                sender_name=sender_name,
                is_active=True
            )
            
            self.add_account(account)
            logger.info(f"✅ Created default email account from environment variables")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating default account: {e}")
            return False