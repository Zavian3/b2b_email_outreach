#!/bin/bash

# 🚀 Quick Deploy Script for Digital Ocean App Platform
# This script helps you deploy your Peekr B2B Automation to Digital Ocean

set -e  # Exit on any error

echo "🎯 Peekr B2B Automation - Digital Ocean Deployment"
echo "================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo -e "${RED}❌ doctl CLI is not installed.${NC}"
    echo "Please install it first:"
    echo "  macOS: brew install doctl"
    echo "  Ubuntu: snap install doctl"
    echo "  Or visit: https://docs.digitalocean.com/reference/doctl/how-to/install/"
    exit 1
fi

# Check if user is authenticated
if ! doctl auth list &> /dev/null; then
    echo -e "${YELLOW}🔐 Please authenticate with Digital Ocean first:${NC}"
    echo "Run: doctl auth init"
    exit 1
fi

echo -e "${GREEN}✅ doctl CLI is ready${NC}"

# Check for required files
required_files=("app.yaml" "Dockerfile" "requirements.txt" "peekr_automation_master.py" "admin_dashboard.py")
missing_files=()

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        missing_files+=("$file")
    fi
done

if [[ ${#missing_files[@]} -gt 0 ]]; then
    echo -e "${RED}❌ Missing required files:${NC}"
    printf '%s\n' "${missing_files[@]}"
    exit 1
fi

echo -e "${GREEN}✅ All required files present${NC}"

# Check for Google credentials
if [[ ! -f "credentials.json" ]]; then
    echo -e "${YELLOW}⚠️  Google credentials file 'credentials.json' not found${NC}"
    echo "Please ensure you have your Google Service Account credentials file."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get app name
read -p "Enter your app name (default: peekr-automation): " app_name
app_name=${app_name:-peekr-automation}

# Update app.yaml with user's GitHub repo
echo -e "${BLUE}📝 Please update app.yaml with your GitHub repository details${NC}"
echo "Current app.yaml content will be updated..."

# Check if user wants to update GitHub repo in app.yaml
read -p "Enter your GitHub username: " github_user
read -p "Enter your repository name: " github_repo

if [[ -n "$github_user" && -n "$github_repo" ]]; then
    # Update app.yaml with actual repo details
    sed -i.bak "s/your-username\/your-repo-name/$github_user\/$github_repo/g" app.yaml
    echo -e "${GREEN}✅ Updated app.yaml with your repository details${NC}"
fi

# Deploy the app
echo -e "${BLUE}🚀 Deploying to Digital Ocean App Platform...${NC}"
echo "This may take 5-10 minutes..."

app_id=$(doctl apps create --spec app.yaml --format ID --no-header)

if [[ -z "$app_id" ]]; then
    echo -e "${RED}❌ Failed to create app${NC}"
    exit 1
fi

echo -e "${GREEN}✅ App created with ID: $app_id${NC}"

# Wait for deployment
echo -e "${BLUE}⏳ Waiting for deployment to complete...${NC}"
echo "You can monitor progress with: doctl apps logs $app_id --follow"

# Check deployment status
max_attempts=30
attempt=1

while [[ $attempt -le $max_attempts ]]; do
    status=$(doctl apps get $app_id --format Phase --no-header)
    
    case $status in
        "ACTIVE")
            echo -e "${GREEN}✅ Deployment successful!${NC}"
            break
            ;;
        "ERROR"|"FAILED")
            echo -e "${RED}❌ Deployment failed${NC}"
            echo "Check logs with: doctl apps logs $app_id"
            exit 1
            ;;
        *)
            echo -e "${YELLOW}⏳ Status: $status (attempt $attempt/$max_attempts)${NC}"
            sleep 30
            ;;
    esac
    
    ((attempt++))
done

if [[ $attempt -gt $max_attempts ]]; then
    echo -e "${YELLOW}⚠️  Deployment is taking longer than expected${NC}"
    echo "Check status with: doctl apps get $app_id"
fi

# Get app URL
app_url=$(doctl apps get $app_id --format LiveURL --no-header)

echo
echo -e "${GREEN}🎉 Deployment completed!${NC}"
echo "================================================="
echo -e "App ID: ${BLUE}$app_id${NC}"
echo -e "Dashboard URL: ${BLUE}$app_url${NC}"
echo -e "Logs: ${BLUE}doctl apps logs $app_id --follow${NC}"
echo

echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Set up environment variables in the DO dashboard:"
echo "   - OPENAI_API_KEY"
echo "   - EMAIL_ACCOUNT and EMAIL_PASSWORD"  
echo "   - SPREADSHEET_ID"
echo "   - APIFY_API_KEY"
echo
echo "2. Upload your Google credentials file if needed"
echo
echo "3. Monitor your application:"
echo "   doctl apps logs $app_id --follow"
echo
echo -e "${GREEN}🚀 Your Peekr B2B Automation is now live!${NC}"