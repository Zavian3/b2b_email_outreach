"""
Email Accounts Manager
Handles CRUD operations for email accounts used in outreach campaigns
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class EmailAccountsManager:
    def __init__(self, accounts_file: str = "email_accounts.json"):
        self.accounts_file = accounts_file
        self.accounts = self.load_accounts()
    
    def load_accounts(self) -> List[Dict]:
        """Load email accounts from JSON file"""
        try:
            if os.path.exists(self.accounts_file):
                with open(self.accounts_file, 'r', encoding='utf-8') as file:
                    accounts = json.load(file)
                    logger.info(f"✅ Loaded {len(accounts)} email accounts")
                    return accounts
            else:
                logger.warning(f"📁 Email accounts file not found: {self.accounts_file}")
                return []
        except Exception as e:
            logger.error(f"❌ Error loading email accounts: {e}")
            return []
    
    def save_accounts(self) -> bool:
        """Save email accounts to JSON file"""
        try:
            with open(self.accounts_file, 'w', encoding='utf-8') as file:
                json.dump(self.accounts, file, indent=2, ensure_ascii=False)
            logger.info(f"💾 Saved {len(self.accounts)} email accounts")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving email accounts: {e}")
            return False
    
    def get_all_accounts(self) -> List[Dict]:
        """Get all email accounts"""
        return self.accounts.copy()
    
    def get_active_account(self) -> Optional[Dict]:
        """Get the currently active email account"""
        for account in self.accounts:
            if account.get('is_active', False):
                return account.copy()
        return None
    
    def get_account_by_id(self, account_id: str) -> Optional[Dict]:
        """Get specific account by ID"""
        for account in self.accounts:
            if account.get('id') == account_id:
                return account.copy()
        return None
    
    def add_account(self, account_data: Dict) -> bool:
        """Add new email account"""
        try:
            # Generate ID if not provided
            if 'id' not in account_data:
                account_data['id'] = f"account-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # Set default values
            account_data.setdefault('created_at', datetime.now().isoformat())
            account_data.setdefault('is_active', False)
            account_data.setdefault('status', 'inactive')
            account_data.setdefault('daily_limit', 100)
            account_data.setdefault('sent_today', 0)
            account_data.setdefault('last_used', None)
            account_data.setdefault('notes', '')
            
            # Validate required fields
            required_fields = ['name', 'email', 'password', 'smtp_server', 'smtp_port', 'imap_server', 'imap_port']
            for field in required_fields:
                if field not in account_data or not account_data[field]:
                    raise ValueError(f"Missing required field: {field}")
            
            self.accounts.append(account_data)
            self.save_accounts()
            logger.info(f"✅ Added new email account: {account_data['email']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding email account: {e}")
            return False
    
    def update_account(self, account_id: str, updates: Dict) -> bool:
        """Update existing email account"""
        try:
            for i, account in enumerate(self.accounts):
                if account.get('id') == account_id:
                    # Don't allow changing ID or created_at
                    updates.pop('id', None)
                    updates.pop('created_at', None)
                    
                    self.accounts[i].update(updates)
                    self.save_accounts()
                    logger.info(f"✅ Updated email account: {account_id}")
                    return True
            
            logger.warning(f"⚠️ Account not found: {account_id}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error updating email account: {e}")
            return False
    
    def delete_account(self, account_id: str) -> bool:
        """Delete email account"""
        try:
            original_count = len(self.accounts)
            self.accounts = [acc for acc in self.accounts if acc.get('id') != account_id]
            
            if len(self.accounts) < original_count:
                self.save_accounts()
                logger.info(f"🗑️ Deleted email account: {account_id}")
                return True
            else:
                logger.warning(f"⚠️ Account not found for deletion: {account_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting email account: {e}")
            return False
    
    def set_active_account(self, account_id: str) -> bool:
        """Set an account as active (deactivates others)"""
        try:
            found = False
            for account in self.accounts:
                if account.get('id') == account_id:
                    account['is_active'] = True
                    account['status'] = 'active'
                    account['last_used'] = datetime.now().isoformat()
                    found = True
                else:
                    account['is_active'] = False
                    account['status'] = 'inactive'
            
            if found:
                self.save_accounts()
                logger.info(f"✅ Set active email account: {account_id}")
                return True
            else:
                logger.warning(f"⚠️ Account not found: {account_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error setting active account: {e}")
            return False
    
    def increment_sent_count(self, account_id: str) -> bool:
        """Increment sent emails count for today"""
        try:
            for account in self.accounts:
                if account.get('id') == account_id:
                    account['sent_today'] = account.get('sent_today', 0) + 1
                    account['last_used'] = datetime.now().isoformat()
                    self.save_accounts()
                    return True
            return False
        except Exception as e:
            logger.error(f"❌ Error incrementing sent count: {e}")
            return False
    
    def reset_daily_counts(self) -> bool:
        """Reset daily sent counts for all accounts (call this daily)"""
        try:
            for account in self.accounts:
                account['sent_today'] = 0
            self.save_accounts()
            logger.info("🔄 Reset daily email counts for all accounts")
            return True
        except Exception as e:
            logger.error(f"❌ Error resetting daily counts: {e}")
            return False
    
    def get_account_stats(self) -> Dict:
        """Get statistics about email accounts"""
        total = len(self.accounts)
        active = sum(1 for acc in self.accounts if acc.get('is_active', False))
        total_sent_today = sum(acc.get('sent_today', 0) for acc in self.accounts)
        
        return {
            'total_accounts': total,
            'active_accounts': active,
            'inactive_accounts': total - active,
            'total_sent_today': total_sent_today
        }
    
    def validate_account_connection(self, account_id: str) -> Dict:
        """Test email account connection (placeholder for actual testing)"""
        account = self.get_account_by_id(account_id)
        if not account:
            return {'success': False, 'message': 'Account not found'}
        
        # TODO: Implement actual SMTP/IMAP connection testing
        return {
            'success': True, 
            'message': 'Connection test not implemented yet',
            'smtp_test': 'pending',
            'imap_test': 'pending'
        }