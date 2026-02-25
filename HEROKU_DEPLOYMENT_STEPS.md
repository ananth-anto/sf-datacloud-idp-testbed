# Heroku Deployment Steps - Quick Reference

Validated steps for deploying to **internal Salesforce Heroku** (and standard Heroku).

## Prerequisites
1. Install Heroku CLI: `brew tap heroku/brew && brew install heroku`
2. Login: `heroku login`

## Step-by-Step Deployment

### 1. Navigate to Project
```bash
cd /path/to/your/project
```
*For this repo: `cd /Users/ananth.anto/Documents/CursorFolder/docai-testbed`*

### 2. Create Heroku App
```bash
heroku create your-app-name
```
*Replace `your-app-name` with a unique name (e.g., `docai-testbed-xyz`)*

### 3. Set Environment Variables
```bash
heroku config:set SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
```
*For this app you do **not** set `LOGIN_URL`, `CLIENT_ID`, or `CLIENT_SECRET` on Heroku — each user enters their org in the app.*

### 3b. Salesforce callback URL (this app only)
After the Heroku app is created, add its callback URL in Salesforce:
1. **Setup** → **Apps** → **App Manager** → open your **Connected App**.
2. Under **Callback URL**, add: `https://your-app-name.herokuapp.com/auth/callback`
3. **Save**.

*Replace `your-app-name` with your actual Heroku app name. Users will use this Connected App when they enter Client ID / Client Secret in the testbed.*

### 4. Ensure Required Files Exist

**Procfile** (in project root) — **for this project**:
```
web: gunicorn app:app
```
*This repo uses `app.py` as the main file and the Flask app variable is `app`. Use `wsgi:app` only if your main file is `wsgi.py`.*

**runtime.txt** (in project root):
```
python-3.11.7
```
*Or use `python-3.11.5` if required by your Heroku stack. Alternatively `.python-version` with `3.11`.*

**requirements.txt** (must exist):
*Must include `flask`, `gunicorn`, `requests`, `python-dotenv`, etc.*

### 5. Important: Check for Naming Conflicts

**CRITICAL**: If you have both:
- A file named `app.py` (or similar)
- A directory named `app/`

**You MUST rename the file** to avoid import conflicts:
```bash
mv app.py wsgi.py
```
*Then update Procfile to match: `web: gunicorn wsgi:app`*

**This project**: There is no `app/` directory, so **keep `app.py`** and use `web: gunicorn app:app` in the Procfile.

### 6. Create .gitignore (if not exists)
```bash
# Python
__pycache__/
*.py[cod]
venv/
env/
.env

# IDE
.vscode/
.idea/

# OS
.DS_Store
```

### 7. Commit and Deploy
```bash
git add .
git commit -m "Prepare for Heroku deployment"
git push heroku main
```
*Use `master` instead of `main` if that's your default branch*

### 8. Verify Deployment
```bash
# Check status
heroku ps --app your-app-name

# Open in browser
heroku open --app your-app-name

# View logs
heroku logs --tail --app your-app-name
```

## Common Issues & Fixes

### Issue: "Failed to find attribute 'app' in 'app'"
**Cause**: Naming conflict between `app.py` file and `app/` directory  
**Fix**: Rename `app.py` to `wsgi.py` and update Procfile

### Issue: App crashes on startup
**Check**: 
- View logs: `heroku logs --tail --app your-app-name`
- Verify Procfile points to correct module
- Ensure all dependencies in requirements.txt

### Issue: Module not found errors
**Fix**: 
- Check all imports in your code
- Ensure requirements.txt includes all dependencies
- Verify file structure matches imports

## Quick Commands Reference

```bash
# Deploy updates
git add .
git commit -m "Your changes"
git push heroku main

# View logs
heroku logs --tail --app your-app-name

# Check app status
heroku ps --app your-app-name

# Open app
heroku open --app your-app-name

# Set config vars
heroku config:set KEY=value --app your-app-name

# View config vars
heroku config --app your-app-name
```

## File Structure Checklist

Before deploying, ensure you have:
- ✅ `Procfile` (for this project: `web: gunicorn app:app`)
- ✅ `requirements.txt` (all dependencies, including `gunicorn`)
- ✅ `runtime.txt` or `.python-version` (Python version)
- ✅ `.gitignore` (excludes `.env`, `access-token.secret`, `venv/`, etc.)
- ✅ Main application file (this project: `app.py`)
- ✅ No naming conflicts between files and directories (this project: no `app/` directory)

## Your App URL

After successful deployment:
`https://your-app-name.herokuapp.com`

For this Document AI testbed, users open the URL → enter Login URL, Client ID, Client Secret → Authenticate with Salesforce → use Analyze Document. See **README.md** or **DEPLOY_HEROKU.md** for full testing steps.

