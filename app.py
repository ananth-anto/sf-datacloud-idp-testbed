from flask import Flask, request, jsonify, render_template, send_file, redirect, render_template_string
import subprocess
import json
import requests
import base64
import logging
import os
from datetime import datetime

# Import configuration
from config import DEFAULT_ML_MODEL, LOGIN_URL, CLIENT_ID, CLIENT_SECRET, API_VERSION, TOKEN_FILE, DOCUMENT_AI_EXTRACT_PATH
from api_client import APIClient

app = Flask("Salesforce Data Cloud Document AI test platform")

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize API client
api_client = APIClient()

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def check_auth_status():
    """Check authentication status"""
    try:
        has_token = api_client.is_authenticated()
        
        return jsonify({
            'serverTime': datetime.now().isoformat(),
            'status': 'running',
            'authenticated': has_token,
            'message': 'Access token found' if has_token else 'Access token not found. Please authenticate first.'
        })
    except Exception as e:
        return jsonify({
            'serverTime': datetime.now().isoformat(),
            'status': 'error',
            'authenticated': False,
            'error': 'Failed to check authentication status',
            'details': str(e)
        }), 500

@app.route('/api/auth-info', methods=['GET'])
def get_auth_info():
    """Get authentication configuration"""
    if not LOGIN_URL or not CLIENT_ID:
        return jsonify({'error': 'Salesforce config missing on server'}), 500
    
    return jsonify({
        'loginUrl': LOGIN_URL,
        'clientId': CLIENT_ID,
    })

@app.route('/auth/callback')
def auth_callback():
    code = request.args.get('code')
    if not code:
        return "Error: No code provided in callback.", 400

    # Render a page that grabs code_verifier from sessionStorage and POSTs it to /auth/exchange
    return render_template_string("""
    <html>
    <body>
    <script>
    const codeVerifier = sessionStorage.getItem('pkce_code_verifier');
    fetch('/auth/exchange', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ code: '{{code}}', code_verifier: codeVerifier })
    }).then(() => {
        window.location = '/';
    });
    </script>
    <p>Completing authentication...</p>
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

    redirect_uri = f"{request.url_root.rstrip('/')}/auth/callback"
    token_url = f"https://{LOGIN_URL}/services/oauth2/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier
    }

    print("Token exchange payload:", payload)
    print("Token URL:", token_url)
    
    resp = requests.post(token_url, data=payload)
    print("Response status:", resp.status_code)
    print("Response headers:", resp.headers)
    print("Response text:", resp.text)
    
    if resp.status_code != 200:
        return f"Error exchanging code for token: {resp.text}", 400

    token_data = resp.json()
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
        
        print('Access token saved successfully')
        
        return jsonify({
            'success': True,
            'message': 'Access token saved successfully'
        })
    except Exception as e:
        print(f'Error saving access token: {e}')
        return jsonify({
            'success': False,
            'error': 'Failed to save access token',
            'details': str(e)
        }), 500

@app.route('/extract-data', methods=['POST'])
def extract_data():
    try:
        if not api_client.is_authenticated():
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
                print(f"Adding schema-level prompt (root description): {config_prompt}")
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

        # Use dynamic instance_url from token file
        instance_url = api_client.get_instance_url()

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
        print(f"Processing document with page range: {page_range if page_range else 'all pages'}")
        if start_page and end_page:
            print(f"Start page: {start_page}, End page: {end_page}")

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

        access_token = api_client.get_access_token()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        print(schema_config)
        logging.info(payload['schemaConfig'])
        logging.info(f"Document AI URL: {url}")

        response = requests.request("POST", url, headers=headers, json=payload, timeout=160)

        # On 404: retry once with path without /actions/ (some instances use different path)
        if response.status_code == 404 and DOCUMENT_AI_EXTRACT_PATH == "ssot/document-processing/actions/extract-data":
            alt_path = "ssot/document-processing/extract-data"
            alt_url = f"{instance_url}/services/data/{API_VERSION}/{alt_path}{query_suffix}"
            logging.info(f"Retrying with alternate path: {alt_url}")
            response = requests.request("POST", alt_url, headers=headers, json=payload, timeout=160)
            if response.status_code in [200, 201]:
                url = alt_url  # for any later error message

        # Handle 404: Document AI endpoint not found
        if response.status_code == 404:
            return jsonify({
                'error': 'Document AI endpoint not found (404)',
                'details': response.text or 'The document-processing API returned 404.',
                'hints': [
                    'Document AI is enabled but the API path may differ on your instance.',
                    'In .env add: DOCUMENT_AI_EXTRACT_PATH=ssot/document-processing/extract-data (path without "actions") and restart.',
                    'Or try API_VERSION=v65.0 or v64.0 in .env in case this endpoint uses a different version.',
                    'Check Data 360 Connect API docs or Postman collection for the current extract-data path.'
                ]
            }), 404
            
        if response.status_code in [200, 201]:
            try:
                # Log raw response for debugging
                logging.debug(f"Raw response: {response.text}")
                
                json_response = response.json()
                logging.debug(f"JSON response: {json.dumps(json_response, indent=2)}")
                
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
    app.run(debug=True, port=3000, host='localhost')