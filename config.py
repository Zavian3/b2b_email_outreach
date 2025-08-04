import os
from dotenv import load_dotenv

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
    def validate_config(cls):
        """Validate that all required environment variables are set"""
        required_vars = [
            'OPENAI_API_KEY', 'EMAIL_ACCOUNT', 'EMAIL_PASSWORD', 
            'SENDER_NAME', 'GOOGLE_CREDENTIALS_FILE', 'SPREADSHEET_ID'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True 