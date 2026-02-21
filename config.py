import os
from dotenv import load_dotenv

load_dotenv()

LOGIN_URL = os.environ.get("LOGIN_URL")
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
API_VERSION = os.environ.get("API_VERSION")
TOKEN_FILE = os.environ.get("TOKEN_FILE", "access-token.secret")
# Optional: override Document AI extract path if default returns 404 (e.g. "ssot/document-processing/extract-data")
DOCUMENT_AI_EXTRACT_PATH = os.environ.get("DOCUMENT_AI_EXTRACT_PATH", "ssot/document-processing/actions/extract-data")

DEFAULT_ML_MODEL = "llmgateway__VertexAIGemini20Flash001"