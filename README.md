# 🚀 Peekr Automated B2B Lead Generation & Outreach System

A comprehensive automated system for B2B lead generation, email outreach, and response management.

## 📁 Project Structure

```
Automated-B2B-Lead-Generation-Outreach/
├── 📊 Lead Generation
│   ├── apify_leads.py          # Enhanced lead generation with Apify
│   └── appify.py               # Legacy Apify integration
│
├── 📧 Email System  
│   ├── emailOutreach.py        # Main email outreach campaigns
│   ├── Smart_email_reply.py    # Intelligent reply handling
│   └── No_reply.py             # Follow-up campaigns
│
├── 🎯 Automation & Management
│   ├── main_scheduler.py       # Central scheduler (MAIN FILE)
│   └── config.py               # Configuration management
│
├── 📝 Templates & Content
│   ├── templates/              # HTML email templates
│   │   ├── peekr_email_template.html
│   │   └── Reply_template.html
│   ├── prompts/                # AI prompt templates
│   │   ├── get_subject_prompt.txt
│   │   ├── classify_prompt.txt
│   │   ├── generate_interested_reply_prompt.txt
│   │   ├── generate_not_interested_reply_prompt.txt
│   │   └── generate_followup_prompt.txt
│   └── prompt_loader.py        # Prompt loading utilities
│
├── ⚙️ Configuration
│   ├── .env                    # Environment variables (sensitive data)
│   ├── .gitignore              # Git ignore rules
│   └── requirements.txt        # Python dependencies
│
└── 📄 Documentation
    └── README.md               # This file
```

## 🔄 Automated Schedule

### 📊 **Lead Generation** 
- **Sunday & Wednesday at 12:00 AM Dubai time** (Saturday/Tuesday 20:00 UTC): Apify scrapes 100+ leads per ALL categories
- Automatically stores results in Google Sheets

### 📧 **Email Outreach**
- **Monday & Thursday at 8:00 AM Dubai time** (04:00 UTC): Send outreach emails to new leads
- Personalized content based on industry and company

### 📡 **Real-Time Reply Monitoring**
- **INSTANT responses**: Monitor emails continuously (24/7)
- **High-volume capable**: Handle hundreds of replies simultaneously
- Intelligent classification (Interested/Not Interested)
- Automated responses based on interest level
- Multi-threaded processing with queue management

### 🔄 **Follow-up Campaigns**
- **Every Monday at 10:00 AM**: Send follow-ups to non-responders
- Smart timing to avoid spam

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment Variables
Create a `.env` file with your credentials:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# Email Configuration  
EMAIL_ACCOUNT=your_email@domain.com
EMAIL_PASSWORD=your_email_password
SMTP_SERVER=your_smtp_server
SMTP_PORT=465

# Google Sheets
GOOGLE_CREDENTIALS_FILE=your_credentials.json
SPREADSHEET_ID=your_spreadsheet_id

# Apify API
APIFY_API_KEY=your_apify_key
```

### 3. Run the System

#### **Automated Mode** (Recommended)
```bash
python main_scheduler.py
```

#### **Manual Testing Mode**
```bash
python main_scheduler.py --test
```

#### **Individual Components**
```bash
# Lead generation only
python apify_leads.py

# Email outreach only  
python emailOutreach.py

# Reply monitoring only
python Smart_email_reply.py

# Follow-up campaigns only
python No_reply.py
```

## 🎯 Key Features

### 🤖 **AI-Powered Email Generation**
- OpenAI GPT-4 for intelligent email content
- Industry-specific pain points and solutions
- Personalized subject lines and content

### 📊 **Smart Lead Management**
- Automated lead validation and scoring
- Duplicate detection and removal
- Industry categorization

### 📧 **Advanced Email Automation**
- Personalized outreach campaigns
- Intelligent reply classification
- Automated follow-up sequences
- Professional HTML templates

### 📈 **Performance Tracking**
- Google Sheets integration for data management
- Real-time campaign monitoring
- Response rate tracking

## ⚙️ Configuration

### Environment Variables
All sensitive data is stored in `.env`:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for content generation |
| `OPENAI_MODEL` | OpenAI model to use (default: gpt-4o-mini) |
| `EMAIL_ACCOUNT` | Sender email address |
| `EMAIL_PASSWORD` | Email account password |
| `SMTP_SERVER` | SMTP server for sending emails |
| `SMTP_PORT` | SMTP port (usually 465 or 587) |
| `GOOGLE_CREDENTIALS_FILE` | Google Service Account JSON file |
| `SPREADSHEET_ID` | Google Sheets ID for data storage |
| `APIFY_API_KEY` | Apify API key for lead generation |

### Google Sheets Setup
Required worksheets:
- **Categories**: Location and category combinations for lead generation
- **Incoming Leads**: Main database of all leads and their status

## 📋 Schedule Customization

Edit `peekr_automation_master.py` to modify schedules:

```python
# Lead generation schedule - 100+ leads per ALL categories (Dubai times converted to UTC)
schedule.every().saturday.at("20:00").do(self.run_apify_lead_generation)    # Sunday 12:00 AM Dubai
schedule.every().tuesday.at("20:00").do(self.run_apify_lead_generation)     # Wednesday 12:00 AM Dubai

# Email outreach schedule (Dubai times converted to UTC)
schedule.every().monday.at("04:00").do(self.run_email_outreach)     # 8:00 AM Dubai
schedule.every().thursday.at("04:00").do(self.run_email_outreach)   # 8:00 AM Dubai
```

## 🛠️ Troubleshooting

### Common Issues

1. **"Missing environment variables"**
   - Ensure `.env` file exists and contains all required variables

2. **"Permission denied" for Google Sheets**
   - Share your spreadsheet with the service account email
   - Verify Google Sheets API is enabled

3. **Email sending failures**
   - Check SMTP credentials and server settings
   - Verify email account allows SMTP access

4. **Apify quota exceeded**
   - Monitor your Apify usage limits
   - Adjust `maxCrawledPlacesPerSearch` in settings

### Logs
Check `scheduler.log` for detailed execution logs and error messages.

## 🔒 Security

- All sensitive data stored in `.env` (not tracked by git)
- Service account authentication for Google Sheets
- Secure SMTP authentication for email sending

## 📞 Support

For issues or questions:
1. Check the logs in `scheduler.log`
2. Verify all environment variables are set correctly
3. Test individual components using manual mode

## 🎉 Success Metrics

The system is designed to:
- Generate **200-400 new leads** twice per week
- Achieve **15-25% email open rates**
- Maintain **professional response handling**
- Operate **24/7 with minimal intervention** 