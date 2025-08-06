import os
from dotenv import load_dotenv
from email_accounts_manager import EmailAccountsManager

# Load environment variables
load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')  # Default to gpt-4o-mini if not specified
    
    # Email Configuration
    EMAIL_ACCOUNT = os.getenv('EMAIL_ACCOUNT')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 465))
    IMAP_SERVER = os.getenv('IMAP_SERVER')
    IMAP_PORT = int(os.getenv('IMAP_PORT', 993))
    
    # Sender Information
    SENDER_NAME = os.getenv('SENDER_NAME')
    SENDER_EMAIL = os.getenv('SENDER_EMAIL')
    
    # Google Sheets Configuration
    GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'peekr-465815-94dae74a243d.json')
    GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON')  # Base64 encoded JSON
    SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
    
    # Apify Configuration
    APIFY_API_KEY = os.getenv('APIFY_API_KEY')
    
    # Timezone Configuration
    TIMEZONE = os.getenv('TIMEZONE', 'Asia/Dubai')  # Default to UAE timezone
    
    # Template Paths
    EMAIL_TEMPLATE_PATH = os.getenv('EMAIL_TEMPLATE_PATH', 'templates/peekr_email_template.html')
    REPLY_TEMPLATE_PATH = os.getenv('REPLY_TEMPLATE_PATH', 'templates/Reply_template.html')
    
    @classmethod
    def get_active_email_config(cls):
        """Get active email account configuration from JSON file"""
        try:
            email_manager = EmailAccountsManager()
            active_account = email_manager.get_active_account()
            
            if active_account:
                return {
                    'EMAIL_ACCOUNT': active_account['email'],
                    'EMAIL_PASSWORD': active_account['password'],
                    'SMTP_SERVER': active_account['smtp_server'],
                    'SMTP_PORT': active_account['smtp_port'],
                    'IMAP_SERVER': active_account['imap_server'],
                    'IMAP_PORT': active_account['imap_port'],
                    'SENDER_NAME': active_account['name'],
                    'SENDER_EMAIL': active_account['email']
                }
            else:
                # Fallback to environment variables if no active account
                return {
                    'EMAIL_ACCOUNT': cls.EMAIL_ACCOUNT,
                    'EMAIL_PASSWORD': cls.EMAIL_PASSWORD,
                    'SMTP_SERVER': cls.SMTP_SERVER,
                    'SMTP_PORT': cls.SMTP_PORT,
                    'IMAP_SERVER': cls.IMAP_SERVER,
                    'IMAP_PORT': cls.IMAP_PORT,
                    'SENDER_NAME': cls.SENDER_NAME,
                    'SENDER_EMAIL': cls.SENDER_EMAIL
                }
        except Exception as e:
            print(f"⚠️ Error loading active email config: {e}")
            # Fallback to environment variables
            return {
                'EMAIL_ACCOUNT': cls.EMAIL_ACCOUNT,
                'EMAIL_PASSWORD': cls.EMAIL_PASSWORD,
                'SMTP_SERVER': cls.SMTP_SERVER,
                'SMTP_PORT': cls.SMTP_PORT,
                'IMAP_SERVER': cls.IMAP_SERVER,
                'IMAP_PORT': cls.IMAP_PORT,
                'SENDER_NAME': cls.SENDER_NAME,
                'SENDER_EMAIL': cls.SENDER_EMAIL
            }
    
    @classmethod
    def validate_config(cls):
        """Validate that all required environment variables are set"""
        # Core required variables
        required_vars = ['OPENAI_API_KEY', 'SPREADSHEET_ID']
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        # Check for Google credentials (either file or JSON)
        if not cls.GOOGLE_CREDENTIALS_FILE and not cls.GOOGLE_CREDENTIALS_JSON:
            missing_vars.append('GOOGLE_CREDENTIALS_JSON (or GOOGLE_CREDENTIALS_FILE)')
        
        # Check for email configuration (either from JSON file or environment variables)
        try:
            email_manager = EmailAccountsManager()
            active_account = email_manager.get_active_account()
            
            if not active_account:
                # No active account in JSON, check environment variables
                email_env_vars = ['EMAIL_ACCOUNT', 'EMAIL_PASSWORD', 'SENDER_NAME']
                for var in email_env_vars:
                    if not getattr(cls, var):
                        missing_vars.append(f"{var} (or configure email account in JSON)")
                        break  # Only report once that email config is missing
        except:
            # JSON file doesn't exist or has issues, check environment variables
            email_env_vars = ['EMAIL_ACCOUNT', 'EMAIL_PASSWORD', 'SENDER_NAME']
            for var in email_env_vars:
                if not getattr(cls, var):
                    missing_vars.append(f"{var} (or configure email account in JSON)")
                    break  # Only report once that email config is missing
        
        if missing_vars:
            raise ValueError(f"Missing required configuration: {', '.join(missing_vars)}")
        
        return True 