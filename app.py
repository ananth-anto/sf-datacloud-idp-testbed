from flask import Flask, request, jsonify, render_template, send_file
import subprocess
import json
import requests
import base64
import logging
import os
from datetime import datetime

# Import configuration
from config import SF_API_URL, DEFAULT_ML_MODEL, LOGIN_URL, CLIENT_ID, INSTANCE_URL, API_VERSION
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
    """OAuth callback page"""
    return send_file('templates/callback.html')

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
        # Check if user is authenticated
        if not api_client.is_authenticated():
            return jsonify({'error': 'Authentication required. Please authenticate with Salesforce first.'}), 401
        
        # Define allowed file extensions
        ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'}
        
        def allowed_file(filename):
            return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed types are: PDF and images (PNG, JPG, JPEG, TIFF, BMP)'}), 400

        # Get schema and model from form data
        schema_config = request.form.get('schema', '')
        ml_model = request.form.get('ml_model', DEFAULT_ML_MODEL)
        
        # Read the file and convert to base64
        file_data = file.read()
        base64_data = base64.b64encode(file_data).decode('utf-8')
        url = SF_API_URL

        payload = {
            "mlModel": ml_model,
            "schemaConfig": json.dumps(json.loads(schema_config)),
            "files": [
                {
                    "mimeType": file.content_type or "image/jpeg",
                    "data": base64_data
                }
            ]
        }

        # Get access token dynamically
        access_token = api_client.get_access_token()
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        print(schema_config)
        logging.info(payload['schemaConfig'])
        
        response = requests.request("POST", url, headers=headers, json=payload, timeout=160)
            
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
                
                # Convert the nested JSON to a string with proper encoding
                formatted_json = json.dumps(nested_json, ensure_ascii=False, indent=2)
                
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
                'details': response.text
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