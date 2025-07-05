import os
import json
from typing import Optional
from config import TOKEN_FILE

class APIClient:
    def __init__(self):
        self.token_file = TOKEN_FILE
    
    def load_access_token(self) -> str:
        """Load access token from local storage"""
        if not os.path.exists(self.token_file):
            raise Exception('Access token not found. Please authenticate with Salesforce first.')
        
        with open(self.token_file, 'r') as f:
            token = f.read().strip()
        
        if not token:
            raise Exception('Access token is empty. Please authenticate with Salesforce first.')
        
        return token
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated with a valid token"""
        try:
            access_token = self.load_access_token()
            return access_token is not None and access_token.strip() != ''
        except Exception:
            return False
    
    def get_access_token(self) -> str:
        """Get the current access token for API calls"""
        return self.load_access_token()
    
    def save_access_token(self, access_token: str) -> None:
        """Save access token to local storage"""
        with open(self.token_file, 'w') as f:
            f.write(access_token.strip()) 