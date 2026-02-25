from flask import Flask, request, jsonify, render_template, send_file, redirect, render_template_string, g, make_response
import subprocess
import json
import requests
import base64
import logging
import os
import secrets
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer, BadSignature

# Import configuration
from config import DEFAULT_ML_MODEL, LOGIN_URL, CLIENT_ID, CLIENT_SECRET, API_VERSION, TOKEN_FILE, DOCUMENT_AI_EXTRACT_PATH
from api_client import APIClient

app = Flask("Salesforce Data Cloud Document AI test platform")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))

# Server-side session store (fallback when cookie not used): session_id -> session dict
SESSIONS = {}
# Cookie-based session: signed payload so it works across Heroku dynos/restarts
SESSION_COOKIE_NAME = "org_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def _session_serializer():
    return URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="org_session")


def _encode_session(data):
    return _session_serializer().dumps(data)


def _decode_session(cookie_val):
    if not cookie_val or len(cookie_val) < 20:
        return None
    try:
        return _session_serializer().loads(cookie_val, max_age=SESSION_MAX_AGE)
    except BadSignature:
        return None


def _get_session_id():
    return getattr(g, "org_session_id", None)


def _get_session():
    return getattr(g, "org_session_data", None)


def _has_env_org():
    return bool(LOGIN_URL and CLIENT_ID and CLIENT_SECRET)


def _set_session_cookie(resp, data):
    """Set the signed session cookie on response."""
    val = _encode_session(data)
    resp.set_cookie(
        SESSION_COOKIE_NAME,
        val,
        max_age=SESSION_MAX_AGE,
        samesite="Lax",
        httponly=True,
        secure=request.is_secure,
    )


@app.before_request
def load_org_session():
    """Load per-user org session from cookie (signed) or in-memory store."""
    g.org_session_id = None
    g.org_session_data = None
    cookie_val = request.cookies.get(SESSION_COOKIE_NAME)
    # Prefer cookie-based session (works across dynos on Heroku)
    decoded = _decode_session(cookie_val)
    if decoded and isinstance(decoded, dict):
        g.org_session_data = decoded
        return
    # Fallback: in-memory by session id (legacy)
    if cookie_val and cookie_val in SESSIONS:
        g.org_session_id = cookie_val
        g.org_session_data = SESSIONS[cookie_val]


def _login_url():
    s = _get_session()
    if s and s.get("login_url"):
        return s["login_url"]
    return LOGIN_URL


def _client_id():
    s = _get_session()
    if s and s.get("client_id"):
        return s["client_id"]
    return CLIENT_ID


def _client_secret():
    s = _get_session()
    if s and s.get("client_secret"):
        return s["client_secret"]
    return CLIENT_SECRET


def _is_authenticated():
    s = _get_session()
    if s and s.get("access_token") and s.get("instance_url"):
        return True
    if _has_env_org():
        try:
            return api_client.is_authenticated()
        except Exception:
            return False
    return False


def _get_access_token():
    s = _get_session()
    if s and s.get("access_token"):
        return s["access_token"]
    return api_client.get_access_token() if api_client.is_authenticated() else None


def _get_instance_url():
    s = _get_session()
    if s and s.get("instance_url"):
        return s["instance_url"]
    return api_client.get_instance_url() if api_client.is_authenticated() else None

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def check_auth_status():
    """Check authentication status. Returns needs_org_config if no org is set (no session and no env)."""
    try:
        # If no session and no env org, user must set org first (e.g. on Heroku)
        if not _get_session() and not _has_env_org():
            return jsonify({
                'serverTime': datetime.now().isoformat(),
                'status': 'running',
                'authenticated': False,
                'needs_org_config': True,
                'message': 'Enter your Salesforce org details to get started.'
            })
        has_token = _is_authenticated()
        return jsonify({
            'serverTime': datetime.now().isoformat(),
            'status': 'running',
            'authenticated': has_token,
            'needs_org_config': False,
            'message': 'Access token found' if has_token else 'Access token not found. Please authenticate first.'
        })
    except Exception as e:
        return jsonify({
            'serverTime': datetime.now().isoformat(),
            'status': 'error',
            'authenticated': False,
            'needs_org_config': False,
            'error': 'Failed to check authentication status',
            'details': str(e)
        }), 500


@app.route('/api/org-config', methods=['POST'])
def set_org_config():
    """Store per-user org configuration (Login URL, Client ID, Client Secret). Isolated per browser via session cookie."""
    try:
        data = request.get_json() or {}
        login_url = (data.get('loginUrl') or '').strip()
        client_id = (data.get('clientId') or '').strip()
        client_secret = (data.get('clientSecret') or '').strip()
        if not login_url or not client_id or not client_secret:
            return jsonify({'error': 'loginUrl, clientId, and clientSecret are required'}), 400
        # Normalize login URL (allow with or without https://)
        if login_url.startswith('https://'):
            login_url = login_url.replace('https://', '', 1)
        session_data = {
            'login_url': login_url,
            'client_id': client_id,
            'client_secret': client_secret,
            'access_token': None,
            'instance_url': None,
        }
        resp = jsonify({'success': True, 'message': 'Org configuration saved.'})
        _set_session_cookie(resp, session_data)
        return resp
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/org-logout', methods=['POST'])
def org_logout():
    """Clear current org session so user can enter a different org."""
    session_id = _get_session_id()
    if session_id and session_id in SESSIONS:
        del SESSIONS[session_id]
    resp = jsonify({'success': True})
    resp.set_cookie(SESSION_COOKIE_NAME, '', max_age=0, expires=0)
    return resp


@app.route('/api/auth-info', methods=['GET'])
def get_auth_info():
    """Get authentication configuration (from session or env)."""
    login_url = _login_url()
    client_id = _client_id()
    if not login_url or not client_id:
        return jsonify({'error': 'Salesforce config missing. Set org details first or configure server.'}), 500
    return jsonify({
        'loginUrl': login_url,
        'clientId': client_id,
    })

@app.route('/auth/callback')
def auth_callback():
    code = request.args.get('code')
    if not code:
        return "Error: No code provided in callback.", 400

    # Render a page that grabs code_verifier from sessionStorage and POSTs it to /auth/exchange
    return render_template_string("""
    <html>
    <head><title>Completing authentication</title></head>
    <body>
    <p id="msg">Completing authentication...</p>
    <p id="err" style="display:none; color:#c00; margin-top:1em;"></p>
    <a id="retry" href="/" style="display:none;">Return to app</a>
    <script>
    const codeVerifier = sessionStorage.getItem('pkce_code_verifier');
    fetch('/auth/exchange', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ code: {{ code|tojson }}, code_verifier: codeVerifier }),
        credentials: 'same-origin'
    }).then(function(res) {
        if (res.ok) {
            window.location = '/';
            return;
        }
        return res.text().then(function(text) {
            document.getElementById('msg').textContent = 'Authentication could not be completed.';
            document.getElementById('err').textContent = text || 'Session may have been lost (e.g. app restarted). Please return and enter your org details again, then click Authenticate.';
            document.getElementById('err').style.display = 'block';
            document.getElementById('retry').style.display = 'inline';
        });
    }).catch(function(e) {
        document.getElementById('msg').textContent = 'Authentication could not be completed.';
        document.getElementById('err').textContent = e.message || 'Network error. Please return and try again.';
        document.getElementById('err').style.display = 'block';
        document.getElementById('retry').style.display = 'inline';
    });
    </script>
    </body>
    </html>
    """, code=code)

@app.route('/auth/exchange', methods=['POST'])
def auth_exchange():
    data = request.get_json()
    code = data.get('code')
    code_verifier = data.get('code_verifier')
    if not code or not code_verifier:
        return "Missing code or code_verifier", 400

    login_url = _login_url()
    client_id = _client_id()
    client_secret = _client_secret()
    if not login_url or not client_id or not client_secret:
        return "Org not configured. Please enter org details first.", 400

    redirect_uri = f"{request.url_root.rstrip('/')}/auth/callback"
    token_url = f"https://{login_url}/services/oauth2/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier
    }

    resp = requests.post(token_url, data=payload)
    if resp.status_code != 200:
        return f"Error exchanging code for token: {resp.text}", 400

    token_data = resp.json()
    session_data = _get_session()
    if session_data is not None:
        session_data["access_token"] = token_data["access_token"]
        session_data["instance_url"] = token_data["instance_url"]
        # Send updated session in cookie so browser has tokens (works across Heroku dynos)
        response = make_response('', 204)
        _set_session_cookie(response, session_data)
        return response
    else:
        # Fallback: write to token file (local dev with .env)
        with open(TOKEN_FILE, "w") as f:
            json.dump({
                "access_token": token_data["access_token"],
                "instance_url": token_data["instance_url"]
            }, f)
        return '', 204

@app.route('/api/save-token', methods=['POST'])
def save_token():
    """Save access token from OAuth callback"""
    try:
        data = request.get_json()
        access_token = data.get('accessToken')
        
        if not access_token:
            return jsonify({
                'success': False,
                'error': 'Access token is required'
            }), 400
        
        # Save the access token
        api_client.save_access_token(access_token)
        
        logging.info("Access token saved successfully")
        
        return jsonify({
            'success': True,
            'message': 'Access token saved successfully'
        })
    except Exception as e:
        logging.warning("Error saving access token: %s", str(e))
        return jsonify({
            'success': False,
            'error': 'Failed to save access token',
            'details': str(e)
        }), 500

@app.route('/extract-data', methods=['POST'])
def extract_data():
    try:
        if not _is_authenticated():
            return jsonify({'error': 'Authentication required. Please authenticate with Salesforce first.'}), 401

        ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'}
        def allowed_file(filename):
            return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed types are: PDF and images (PNG, JPG, JPEG, TIFF, BMP)'}), 400

        schema_config = request.form.get('schema', '')
        ml_model = request.form.get('ml_model', DEFAULT_ML_MODEL)
        include_confidence = request.form.get('include_confidence') == 'true'
        page_range = request.form.get('page_range', '').strip()
        config_prompt = request.form.get('config_prompt', '').strip()
        file_data = file.read()
        base64_data = base64.b64encode(file_data).decode('utf-8')
        
        # Schema-level instructions: Document AI uses the root-level "description" of the schema JSON.
        try:
            schema_json = json.loads(schema_config)
            if config_prompt:
                schema_json['description'] = config_prompt
                logging.info("Schema-level prompt added (root description)")
            schema_config_final = json.dumps(schema_json)
        except json.JSONDecodeError as e:
            return jsonify({'error': f'Invalid JSON schema: {str(e)}'}), 400

        # Parse page range if provided
        start_page = None
        end_page = None

        if page_range:
            try:
                parts = page_range.split('-')
                if len(parts) == 2:
                    start_page = int(parts[0])
                    end_page = int(parts[1])
                    
                    # Validate
                    if start_page < 1 or end_page < 1:
                        return jsonify({'error': 'Page numbers must be at least 1'}), 400
                    if start_page > end_page:
                        return jsonify({'error': 'Start page must be less than or equal to end page'}), 400
                else:
                    return jsonify({'error': 'Invalid page range format. Use: startPage-endPage'}), 400
            except ValueError:
                return jsonify({'error': 'Invalid page range format. Use: startPage-endPage'}), 400

        instance_url = _get_instance_url()

        # Build query parameters (reused for retry)
        query_params = []
        if include_confidence:
            query_params.append('extractDataWithConfidenceScore=true')
        if start_page is not None:
            query_params.append(f'startPage={start_page}')
        if end_page is not None:
            query_params.append(f'endPage={end_page}')
        query_suffix = '?' + '&'.join(query_params) if query_params else ''

        # Build URL: support override via DOCUMENT_AI_EXTRACT_PATH (some orgs use path without /actions/)
        path_suffix = DOCUMENT_AI_EXTRACT_PATH.strip().strip('/')
        url = f"{instance_url}/services/data/{API_VERSION}/{path_suffix}{query_suffix}"

        # Log page range for debugging
        logging.info("Processing document (page_range=%s)", page_range or "all")

        payload = {
            "mlModel": ml_model,
            "schemaConfig": schema_config_final,
            "files": [
                {
                    "mimeType": file.content_type or "image/jpeg",
                    "data": base64_data
                }
            ]
        }

        access_token = _get_access_token()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        # Do not log schema, payload, or URL (may contain user data or org identity)
        response = requests.request("POST", url, headers=headers, json=payload, timeout=160)

        # On 404: try alternate path and/or API version (different orgs use different combinations)
        if response.status_code == 404:
            paths = [
                "ssot/document-processing/actions/extract-data",
                "ssot/document-processing/extract-data",
            ]
            versions = list(dict.fromkeys([API_VERSION, "v65.0", "v64.0"]))  # dedupe, keep order
            for try_version in versions:
                for try_path in paths:
                    if try_path == path_suffix and try_version == API_VERSION:
                        continue  # already tried above
                    alt_url = f"{instance_url}/services/data/{try_version}/{try_path}{query_suffix}"
                    logging.info("Retrying 404 with alternate path/version")
                    response = requests.request("POST", alt_url, headers=headers, json=payload, timeout=160)
                    if response.status_code in [200, 201]:
                        url = alt_url
                        break
                if response.status_code in [200, 201]:
                    break

        # Handle 404: Document AI endpoint not found
        if response.status_code == 404:
            return jsonify({
                'error': 'Document AI endpoint not found (404)',
                'details': response.text or 'The document-processing API returned 404.',
                'hints': [
                    'Document AI may not be enabled in this org, or the API path/version differs.',
                    'Confirm Document AI is enabled: Setup → Data 360 Connect / Document AI.',
                    'On Heroku set: DOCUMENT_AI_EXTRACT_PATH=ssot/document-processing/extract-data or .../actions/extract-data, and API_VERSION=v65.0 or v64.0.',
                    'Check Data 360 Connect API docs or Postman for the current extract-data path for your org.'
                ]
            }), 404
            
        if response.status_code in [200, 201]:
            try:
                # Do not log response body (may contain extracted PII or sensitive data)
                json_response = response.json()
                
                # Check if response has expected structure
                if not json_response:
                    return jsonify({'error': 'Empty response from server'}), 200
                
                if 'data' not in json_response or not json_response['data']:
                    return jsonify({'error': 'No data in response'}), 200
                
                # Check for error in the response
                if json_response['data'][0].get('error'):
                    error_msg = json_response['data'][0]['error']
                    if '403' in error_msg:
                        return jsonify({
                            'error': 'Authentication error with the OpenAI service. Please check your API credentials.',
                            'details': error_msg
                        }), 403
                    return jsonify({
                        'error': 'Service error',
                        'details': error_msg
                    }), 500
                
                nested_json_str = json_response['data'][0].get('data')
                if not nested_json_str:
                    return jsonify({'error': 'No extracted data in response'}), 200
                
                # Replace HTML entities
                nested_json_str = nested_json_str.replace('&quot;', '"').replace('&#92;', '\\')
                
                # Parse the JSON string
                nested_json = json.loads(nested_json_str)
                
                # Unified response shape: always { data, metadata?, apiRequest? }
                response_data = {'data': nested_json}
                if include_confidence:
                    response_data['metadata'] = {'confidenceScoresIncluded': True}
                
                # Build developer snippet (curl + Apex) for successful extract-data
                payload_json = json.dumps(payload, ensure_ascii=False)
                # Escape single quotes for use inside single-quoted curl -d '...'
                def escape_single_quotes(s):
                    return s.replace("'", "'\"'\"'")
                payload_escaped = escape_single_quotes(payload_json)
                url_escaped = escape_single_quotes(url)
                token_escaped = escape_single_quotes(access_token)
                curl_cmd = f"curl -X POST '{url_escaped}' -H 'Content-Type: application/json' -H 'Authorization: Bearer {token_escaped}' -d '{payload_escaped}'"
                
                mime_type = file.content_type or 'image/jpeg'
                apex_endpoint = f"{instance_url.rstrip('/')}/services/data/{API_VERSION}/ssot/document-processing/actions/extract-data{query_suffix}"
                apex_snippet = f'''HttpRequest req = new HttpRequest();
req.setEndpoint('{apex_endpoint}');
req.setMethod('POST');
req.setHeader('Content-Type', 'application/json');
req.setHeader('Authorization', 'Bearer ' + accessToken);
req.setBody('{{"mlModel":"{ml_model}","schemaConfig":' + schemaConfigJson + ',"files":[{{"mimeType":"{mime_type}","data":"' + base64FileData + '"}}]}}');
Http http = new Http();
HttpResponse res = http.send(req);
// Replace: accessToken, schemaConfigJson (JSON string), base64FileData (Base64 string).'''
                
                response_data['apiRequest'] = {
                    'curl': curl_cmd,
                    'apex': apex_snippet
                }
                
                formatted_json = json.dumps(response_data, ensure_ascii=False, indent=2)
                return formatted_json, 200, {
                    'Content-Type': 'application/json; charset=utf-8'
                }
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                return jsonify({
                    'error': f'Error processing response: {str(e)}',
                    'raw_response': response.text
                }), 500
        else:
            return jsonify({
                'error': f'API request failed with status {response.status_code}',
                'details': response.text,
                'url_used': url
            }), response.status_code

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/json-jazz')
def json_jazz():
    return render_template('json-jazz.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug, port=port, host='0.0.0.0')