# Step-by-step: Deploy to Heroku and test

Follow these steps in order to deploy the Document AI testbed to Heroku and verify it works.

> **Validated reference:** For deployment to **internal Salesforce Heroku**, use **HEROKU_DEPLOYMENT_STEPS.md** as the canonical quick reference (Procfile, SECRET_KEY, naming, common issues). This file adds app-specific steps (commit, callback URL, testing).

---

## Prerequisites

- **Git** – repo is already a git repo
- **Heroku CLI** – [Install](https://devcenter.heroku.com/articles/heroku-cli) then run `heroku login`
- **Salesforce Connected App** – You’ll use its Client ID and Client Secret (and your org’s login URL) in the app after deploy

---

## Step 1: Commit everything

From the project root:

```bash
cd /Users/ananth.anto/Documents/CursorFolder/docai-testbed

git status
git add app.py config.py api_client.py requirements.txt Procfile runtime.txt templates/ static/ .env.example README.md DEPLOY_HEROKU.md
# Do NOT add .env or access-token.secret (they are in .gitignore)
git commit -m "Add Heroku deploy and per-user org config"
```

If you already committed these files, ensure there are no uncommitted changes:

```bash
git status
```

---

## Step 2: Create the Heroku app

**Option A – You choose the name (must be unique on Heroku):**

```bash
heroku create docai-testbed-xyz
```

Replace `docai-testbed-xyz` with any available name (e.g. `docai-testbed-yourname`).

**Option B – Heroku picks the name:**

```bash
heroku create
```

Note the app URL from the output, e.g. `https://docai-testbed-xyz.herokuapp.com/`. You’ll need it for the Salesforce callback URL.

---

## Step 3: Deploy to Heroku

Push your branch (usually `main` or `master`):

```bash
git push heroku main
```

If your default branch is `master`:

```bash
git push heroku master
```

Wait for the build to finish. You should see “Building…” then “Launching…” and “Deployed to Heroku”.

---

## Step 4: Add callback URL in Salesforce

1. In Salesforce: **Setup** → **Apps** → **App Manager** → open your **Connected App**.
2. Under **API (Enable OAuth Settings)** ensure:
   - **Enable OAuth Settings** is checked.
   - **Callback URL** includes your Heroku URL with path `/auth/callback`.

   Add this line (replace with your real Heroku app URL):

   ```
   https://YOUR-HEROKU-APP-NAME.herokuapp.com/auth/callback
   ```

   Example: if the app is `docai-testbed-xyz`, use:

   ```
   https://docai-testbed-xyz.herokuapp.com/auth/callback
   ```

   You can keep `http://localhost:3000/auth/callback` for local testing.

3. **Save** the Connected App.

---

## Step 5: (Optional) Set SECRET_KEY on Heroku

For session cookie security:

```bash
heroku config:set SECRET_KEY=$(openssl rand -hex 32)
```

Confirm it’s set (value is hidden):

```bash
heroku config
```

---

## Step 6: Open the app in the browser

```bash
heroku open
```

Your browser should open `https://YOUR-APP-NAME.herokuapp.com/`.

---

## Step 7: Test the flow

1. **Org setup (first time)**  
   You should see the modal **“Set up your Salesforce org”**.  
   - **Login URL:** e.g. `yourdomain.my.salesforce.com` or `test.salesforce.com` for sandbox.  
   - **Client ID:** from your Connected App (Consumer Key).  
   - **Client Secret:** from your Connected App (Consumer Secret).  
   Click **Save and continue**.

2. **Authenticate**  
   Click **“Authenticate with Salesforce”**.  
   - You should be redirected to Salesforce login.  
   - Log in and allow the app.  
   - You should return to the testbed with “Authenticated with Salesforce” and the **Analyze Document** button enabled.

3. **Run an extraction**  
   - Upload a small PDF or image.  
   - Paste a simple JSON schema (e.g. `{"type":"object","properties":{"name":{"type":"string"}}}`).  
   - Click **Analyze Document**.  
   - You should get a result (or a clear API error), confirming the app and your org are working.

4. **“Use a different org”**  
   Click **Use a different org**. The org setup modal should appear again; you can enter another org or the same one to confirm the flow.

---

## Step 8: Check logs if something fails

```bash
heroku logs --tail
```

Leave this running in a terminal while you reproduce the issue. Look for Python tracebacks or 4xx/5xx responses.

---

## Quick reference

| Task              | Command |
|-------------------|--------|
| Open app          | `heroku open` |
| View config       | `heroku config` |
| View logs         | `heroku logs --tail` |
| Restart dyno      | `heroku restart` |
| App URL           | `heroku info` (or Dashboard) |

---

## Callback URL format

- **Heroku:** `https://YOUR-APP-NAME.herokuapp.com/auth/callback`  
- **Local:** `http://localhost:3000/auth/callback`

Use **HTTPS** for Heroku and **HTTP** for localhost.

---

## If deploy or run fails

- **Build fails:** Ensure `Procfile`, `runtime.txt`, and `requirements.txt` are committed and that `requirements.txt` includes `gunicorn`.
- **App crash / 503:** Run `heroku logs --tail` and fix any missing dependency or runtime error.
- **“Org not configured” after saving:** Ensure you clicked **Save and continue** and that the modal closed; then click **Authenticate with Salesforce**.
- **OAuth error / redirect issue:** Confirm the exact callback URL in the Connected App matches your Heroku URL (including `https://` and `/auth/callback`).
