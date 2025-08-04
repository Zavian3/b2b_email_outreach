# 🔑 RECOVER Google Credentials - Quick Guide

## 🚨 **I Accidentally Deleted Your `peekr-465815-94dae74a243d.json` File!**

**Don't worry, we can get it back from Google Cloud Console.**

### **Step 1: Find Your Existing Service Account**

1. **Go to Google Cloud Console**: https://console.cloud.google.com/iam-admin/serviceaccounts
2. **Select your project** (likely named "peekr" or similar)
3. **Find your existing service account** (probably already exists)

### **Step 2: Download New Credentials**

1. **Click on your existing service account**
2. **Go to "Keys" tab**
3. **Click "Add Key" → "Create new key"**
4. **Choose "JSON" format**
5. **Click "Create"** 
6. **Rename the downloaded file to `peekr-465815-94dae74a243d.json`** 
7. **Place it in your project directory**

⚠️ **IMPORTANT**: The new file will have a different name, but rename it to `peekr-465815-94dae74a243d.json` so our code works.

### **Step 3: Enable APIs (if not done already)**

1. **Go to**: https://console.cloud.google.com/apis/library
2. **Enable these APIs**:
   - Google Sheets API
   - Google Drive API

### **Step 4: Share Your Google Sheet**

1. **Open your Google Sheet**
2. **Click "Share"**
3. **Add the service account email** (from credentials.json)
4. **Give "Editor" permissions**

### **Step 5: Test Credentials**

```bash
# Place credentials.json in your project directory
python credentials_helper.py
```

---

## 🔐 **For Digital Ocean Deployment:**

Once you have `credentials.json`:

```bash
# Encode credentials for DO
python encode_credentials.py
```

This will give you a base64 string to add as `GOOGLE_CREDENTIALS_JSON` environment variable in Digital Ocean.

---

## 📋 **Quick Checklist:**

- [ ] Downloaded `credentials.json`
- [ ] Enabled Google Sheets & Drive APIs  
- [ ] Shared Google Sheet with service account email
- [ ] Tested credentials with `python credentials_helper.py`
- [ ] Encoded for deployment with `python encode_credentials.py`

---

## 🆘 **If You're Stuck:**

**The service account email** looks like:
`your-service-account@your-project.iam.gserviceaccount.com`

**Find it in the credentials.json file** under `"client_email"`