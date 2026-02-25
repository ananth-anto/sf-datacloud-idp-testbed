# Security notes

## Before committing to GitHub

- **Never commit:** `.env`, `access-token.secret`, or any file containing real credentials, tokens, or PII.
- **Verify:** Run `git status` and `git diff --staged` before pushing. Ensure `.env` and `access-token.secret` are listed in `.gitignore` and do **not** appear as staged files.

## PII and secrets

- **.env** – Contains `LOGIN_URL`, `CLIENT_ID`, `CLIENT_SECRET`. Must remain in `.gitignore`. Only `.env.example` (placeholders only) may be committed.
- **access-token.secret** – Contains OAuth tokens and instance URL. In `.gitignore`; do not commit.
- **No hardcoded credentials** – The app reads org config from environment (local) or from the per-user signed cookie (Heroku). No secrets are hardcoded in source.

## One user’s secret never used for another

- **Session isolation:** Each user’s org config and tokens are stored in a **signed cookie** (`org_session`) that is set and read only for that user’s browser. The server does not store sessions in a shared key-value store that could be queried by another user.
- **Request scope:** `load_org_session()` runs per request and only ever reads the cookie for that request. There is no API that returns one user’s session to another user.
- **Developer reference (curl/Apex):** The access token is included in the API response only for the **same** request that performed the extraction (so the user can copy their own curl). It is not stored in logs or shared.

## Secrets not logged (app and Heroku)

- **No logging of:** `client_secret`, `access_token`, full request/response bodies that could contain credentials or extracted PII.
- **Redacted/removed:** `print()` and `logging` of schema config, payload, Document AI URL (org identity), and raw Document AI response have been removed or replaced with safe messages (e.g. “Document AI request sent”, “Retrying 404 with alternate path/version”).
- **Token exchange:** The `/auth/exchange` error response returns Salesforce’s error text to the client only; it is not logged on the server.
- **OAuth callback URL:** `gunicorn_config.py` uses a custom logger that redacts the `code` query parameter in `/auth/callback` so app access logs show `code=[REDACTED]`. (Heroku router may still log the full URL; OAuth codes are single-use and short-lived.)
- **Heroku:** Config vars (e.g. `SECRET_KEY`, `DOCUMENT_AI_EXTRACT_PATH`) are not printed or logged. Application logs do not contain credentials or tokens.

## Legacy / unused

- **templates/callback.html** – Legacy template for an old callback flow. The live app uses `render_template_string` in `app.py` for `/auth/callback` (PKCE). This template must not display or log the access token; it has been updated so the token is not shown in the DOM or console.

## Quick verification before push

```bash
git status
git diff --staged
# Confirm .env and access-token.secret are NOT in the list of files to be committed.
git check-ignore -v .env access-token.secret
# Should show both files are ignored.
```
