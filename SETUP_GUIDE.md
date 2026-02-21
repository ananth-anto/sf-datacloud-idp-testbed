# Quick Setup Guide

This guide will help you get the Salesforce Data Cloud Document AI Testbed running in just a few minutes.

## Key Features

- **Confidence Scores**: Optional accuracy indicators for each extracted field with color-coded display (Green: ≥0.8, Yellow: 0.5-0.79, Red: <0.5)
- **Page Range Selection**: Process specific pages from PDF documents (e.g., 1-5, 3-10)
- **Multiple ML Models**: Choose between Gemini Fast and OpenAI GPT-4o
- **OAuth Authentication**: Secure PKCE-based authentication flow
- **Custom Schemas**: Define your own extraction patterns with JSON schemas

## Prerequisites
- Python 3.7 or higher
- A Salesforce org with Data Cloud enabled
- A Salesforce Connected App configured for OAuth

## Step-by-Step Setup

### 1. Clone and Navigate
```bash
git clone https://github.com/ananth-anto/sf-datacloud-idp-testbed
cd sf-datacloud-idp-testbed
```

### 2. Create Your .env File (CRITICAL STEP)
```bash
cp .env.example .env
```

### 3. Configure Your Credentials
Open the `.env` file in your text editor and replace these values:

```env
LOGIN_URL=your-actual-domain.my.salesforce.com
CLIENT_ID=paste-your-client-id-here
CLIENT_SECRET=paste-your-client-secret-here
API_VERSION=v64.0
TOKEN_FILE=access-token.secret
```

**Where to find these values:**
- **LOGIN_URL**: Your Salesforce domain (e.g., `login.salesforce.com` or custom domain)
- **CLIENT_ID & CLIENT_SECRET**: From Setup → Apps → App Manager → [Your Connected App] → View

### 4. Set Up Python Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 5. Run the Application
```bash
python app.py
```

The application will start at: **http://localhost:3000**

### 6. First Use
1. Open http://localhost:3000 in your browser
2. Click "Authenticate with Salesforce"
3. Log in with your Salesforce credentials
4. Grant permissions when prompted
5. Upload a document and enter a JSON schema
6. **Optional**: Check "Include Confidence Scores" to see accuracy indicators
7. Click "Analyze Document" to process
8. View results with color-coded confidence scores (if enabled)

## Common Errors and Solutions

### ❌ "Salesforce configuration missing on server"
**Problem**: The `.env` file doesn't exist or has placeholder values

**Solution**: 
1. Make sure you created `.env` file: `ls -la .env`
2. Open `.env` and verify it has your actual credentials (not placeholders)
3. Restart the Flask application

### ❌ "No such file or directory: .env"
**Problem**: You didn't create the `.env` file

**Solution**: Run `cp .env.example .env` and then edit it with your credentials

### ❌ Port 3000 already in use
**Problem**: Another process is using port 3000

**Solution**: 
```bash
# Find and kill the process
lsof -ti:3000 | xargs kill -9

# Or run on a different port by modifying app.py
```

## Need Help?

- Check the full [README.md](README.md) for detailed documentation
- See the [Troubleshooting section](README.md#troubleshooting) for more solutions
- Watch the [YouTube walkthrough](https://youtu.be/H8cgvUP7Ytg)

## Connected App Setup

If you haven't created a Connected App yet:

1. Go to Setup → Apps → App Manager → New Connected App
2. Fill in basic information
3. Enable OAuth Settings
4. Set Callback URL: `http://localhost:3000/auth/callback`
5. Select OAuth Scopes:
   - Full access (full)
   - Perform requests at any time (refresh_token, offline_access)
6. Save and wait 2-10 minutes for changes to propagate
7. Click "Manage Consumer Details" to get your Client ID and Secret

---

**Ready to go!** Once setup is complete, you can upload documents and extract structured data using custom JSON schemas.
