# Deploy with App Spec - Step by Step

## Method 1: DigitalOcean Dashboard with App Spec

1. **Go to**: https://cloud.digitalocean.com/apps
2. **Click "Create App"**
3. **Choose "Import from App Spec"** (instead of GitHub)
4. **Paste this complete spec**:

```yaml
name: peekr-automation-complete
services:
- name: dashboard-and-automation
  source_dir: /
  github:
    repo: Zavian3/b2b_email_outreach
    branch: main
    deploy_on_push: true
  build_command: pip install -r requirements.txt
  run_command: python3 combined_app.py
  environment_slug: python
  engines:
    python: "3.11.5"
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 8080
  routes:
  - path: /
```

5. **Add your environment variables in the dashboard**
6. **Deploy**

## Method 2: Using doctl CLI

```bash
# Install doctl if not already installed
# macOS: brew install doctl

# Authenticate
doctl auth init

# Create app from spec
doctl apps create --spec app.yaml

# Monitor deployment
doctl apps list
```

This forces Digital Ocean to use your app.yaml specification instead of auto-detection.