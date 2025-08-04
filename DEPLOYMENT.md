# 🚀 Digital Ocean Deployment Guide

This guide covers multiple ways to deploy your Peekr B2B Automation System to Digital Ocean.

## 📋 Prerequisites

1. Digital Ocean account
2. GitHub repository with your code
3. Google Service Account credentials file
4. Required API keys (OpenAI, Apify, etc.)

## 🎯 **Option 1: App Platform (Recommended - GitHub Integration)**

### Step 1: Prepare Your Repository

1. **Add deployment files** (already created):
   - `app.yaml` - App Platform configuration
   - `Dockerfile` - Container definition
   - `requirements.txt` - Updated with all dependencies

2. **Create `.env` file** (don't commit this):
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Upload Google Credentials**:
   - Add your `credentials.json` file to the root directory
   - Or use Digital Ocean Spaces and reference the URL

### Step 2: Deploy via App Platform

#### Method A: Using the Web Interface

1. Go to [Digital Ocean App Platform](https://cloud.digitalocean.com/apps)
2. Click "Create App"
3. Choose "GitHub" as source
4. Select your repository and branch
5. Configure services:
   - **Automation Engine**: Worker service running `peekr_automation_master.py`
   - **Admin Dashboard**: Web service running `admin_dashboard.py`

#### Method B: Using CLI (Faster)

```bash
# Install doctl CLI
# macOS: brew install doctl
# Ubuntu: snap install doctl

# Authenticate
doctl auth init

# Create app from spec
doctl apps create --spec app.yaml

# Monitor deployment
doctl apps list
doctl apps logs <app-id> --follow
```

### Step 3: Configure Environment Variables

Add these secrets in the App Platform dashboard:

```
OPENAI_API_KEY=your_key_here
EMAIL_ACCOUNT=your_email@gmail.com  
EMAIL_PASSWORD=your_app_password
SPREADSHEET_ID=your_sheet_id
APIFY_API_KEY=your_apify_key
```

### Step 4: Access Your Application

- **Admin Dashboard**: `https://your-app-name.ondigitalocean.app`
- **Automation Engine**: Runs in background automatically

---

## 🖥️ **Option 2: Digital Ocean Droplets (More Control)**

### Step 1: Create a Droplet

```bash
# Create Ubuntu 22.04 droplet
doctl compute droplet create \
  --image ubuntu-22-04-x64 \
  --size s-2vcpu-2gb \
  --region nyc1 \
  peekr-automation
```

### Step 2: SSH and Setup

```bash
# SSH into droplet
ssh root@your_droplet_ip

# Update system
apt update && apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
apt install docker-compose -y

# Install Git
apt install git -y

# Clone your repository
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### Step 3: Configure Environment

```bash
# Create .env file
nano .env
# Add all your environment variables

# Upload your Google credentials
# You can use scp from your local machine:
# scp credentials.json root@your_droplet_ip:/path/to/repo/
```

### Step 4: Deploy with Docker Compose

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Step 5: Setup Nginx (Optional - for custom domain)

```bash
# Install Nginx
apt install nginx -y

# Create Nginx config
cat > /etc/nginx/sites-available/peekr <<EOF
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/peekr /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

---

## ☸️ **Option 3: Digital Ocean Kubernetes (Advanced)**

### Step 1: Create Kubernetes Cluster

```bash
# Create cluster
doctl kubernetes cluster create peekr-cluster \
  --region nyc1 \
  --node-pool "name=worker-pool;size=s-2vcpu-2gb;count=2"

# Get kubeconfig
doctl kubernetes cluster kubeconfig save peekr-cluster
```

### Step 2: Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace peekr

# Create ConfigMap for environment variables
kubectl create configmap peekr-config \
  --from-env-file=.env \
  --namespace=peekr

# Apply Kubernetes manifests
kubectl apply -f k8s/ --namespace=peekr
```

---

## 🔧 **Configuration & Monitoring**

### Environment Variables

Create a `.env` file with these variables:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Email Configuration  
EMAIL_ACCOUNT=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993

# Sender Information
SENDER_NAME=Your Name
SENDER_EMAIL=your_email@gmail.com

# Google Sheets Configuration
GOOGLE_CREDENTIALS_FILE=credentials.json
SPREADSHEET_ID=your_google_sheet_id

# Apify Configuration
APIFY_API_KEY=your_apify_api_key

# Timezone Configuration
TIMEZONE=Asia/Dubai
```

### Monitoring Commands

```bash
# App Platform
doctl apps logs <app-id> --follow
doctl apps list

# Docker Compose (Droplet)
docker-compose logs -f automation-engine
docker-compose logs -f admin-dashboard
docker-compose ps

# Kubernetes
kubectl logs -f deployment/peekr-automation -n peekr
kubectl get pods -n peekr
```

### SSL/HTTPS Setup

For custom domains:

```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Get SSL certificate
certbot --nginx -d your-domain.com

# Auto-renewal
crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 🚨 **Security Considerations**

1. **Environment Variables**: Use Digital Ocean's secret management
2. **Network**: Configure firewalls and VPC
3. **Access**: Use SSH keys, disable password authentication
4. **Updates**: Regular security updates
5. **Backup**: Database and configuration backups

### Firewall Setup (Droplet)

```bash
# Enable UFW
ufw enable

# Allow SSH
ufw allow ssh

# Allow HTTP/HTTPS
ufw allow 80
ufw allow 443

# Allow Streamlit (if needed)
ufw allow 8501

# Check status
ufw status
```

---

## 📊 **Scaling & Performance**

### Vertical Scaling
- App Platform: Upgrade instance size
- Droplet: Resize droplet
- Kubernetes: Adjust resource requests/limits

### Horizontal Scaling
- App Platform: Increase instance count
- Kubernetes: Increase replica count
- Load balancer for multiple instances

### Monitoring
- Digital Ocean Monitoring
- Application logs
- Performance metrics
- Alert notifications

---

## 🔄 **CI/CD with GitHub Actions**

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Digital Ocean

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to App Platform
      uses: digitalocean/app_action@v1
      with:
        app_name: peekr-automation
        token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
```

---

## 📞 **Support & Troubleshooting**

### Common Issues

1. **Google Sheets Access**: Verify credentials and sheet permissions
2. **Email Authentication**: Use app passwords for Gmail
3. **Memory Limits**: Monitor resource usage
4. **Timezone Issues**: Verify TIMEZONE environment variable

### Debug Commands

```bash
# Check logs
docker-compose logs automation-engine | tail -100

# Test connectivity
docker-compose exec automation-engine python -c "import requests; print(requests.get('https://google.com').status_code)"

# Verify environment
docker-compose exec automation-engine env | grep -E "(OPENAI|EMAIL|APIFY)"
```

---

## 💰 **Cost Estimation**

### App Platform
- Basic: ~$5-12/month per service
- Recommended: ~$24/month for both services

### Droplets  
- Basic (2GB RAM): ~$12/month
- Recommended (4GB RAM): ~$24/month

### Additional Costs
- Load Balancer: ~$10/month
- Spaces (backup): ~$5/month
- Monitoring: Free with droplets

---

Choose the deployment method that best fits your needs:
- **App Platform**: Easiest, automatic scaling, GitHub integration
- **Droplets**: More control, custom configurations  
- **Kubernetes**: Advanced features, enterprise-scale

Need help? Check the troubleshooting section or create an issue in your repository.