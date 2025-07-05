import os
from dotenv import load_dotenv

load_dotenv()

# Salesforce API configuration
SF_API_URL = f"{os.environ.get('INSTANCE_URL')}/services/data/{os.environ.get('API_VERSION')}/ssot/document-processing/actions/extract-data"

# OAuth Configuration
LOGIN_URL = os.environ.get("LOGIN_URL")
CLIENT_ID = os.environ.get("CLIENT_ID")
INSTANCE_URL = os.environ.get("INSTANCE_URL")
API_VERSION = os.environ.get("API_VERSION")

# Token storage configuration
TOKEN_FILE = os.environ.get("TOKEN_FILE", "access-token.secret")

# Default model configuration
DEFAULT_ML_MODEL = os.environ.get("DEFAULT_ML_MODEL")
