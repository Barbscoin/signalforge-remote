import json
from pathlib import Path
from cryptography.fernet import Fernet
import os


class SecureStore:
    """Encrypted credential storage"""
    
    def __init__(self, store_path="credentials.json", key_path=".store_key"):
        self.store_path = Path(store_path)
        self.key_path = Path(key_path)
        self.cipher = self._get_cipher()
    
    def _get_cipher(self):
        """Get or create encryption cipher"""
        if self.key_path.exists():
            with open(self.key_path, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_path, 'wb') as f:
                f.write(key)
        return Fernet(key)
    
    def _load_store(self):
        """Load credentials from file"""
        if self.store_path.exists():
            try:
                with open(self.store_path, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_store(self, data):
        """Save credentials to file"""
        with open(self.store_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def encrypt_password(self, password: str) -> str:
        """Encrypt a password"""
        return self.cipher.encrypt(password.encode()).decode()
    
    def decrypt_password(self, encrypted: str) -> str:
        """Decrypt a password"""
        return self.cipher.decrypt(encrypted.encode()).decode()
    
    def store_credential(self, name: str, credential_type: str, value: str):
        """Store a credential (password, API key, SSH key, etc)"""
        data = self._load_store()
        encrypted = self.encrypt_password(value)
        if name not in data:
            data[name] = {}
        data[name][credential_type] = encrypted
        self._save_store(data)
    
    def get_credential(self, name: str, credential_type: str) -> str:
        """Retrieve a credential"""
        data = self._load_store()
        if name in data and credential_type in data[name]:
            encrypted = data[name][credential_type]
            return self.decrypt_password(encrypted)
        return None
    
    def delete_credential(self, name: str, credential_type: str = None):
        """Delete a credential"""
        data = self._load_store()
        if name in data:
            if credential_type:
                if credential_type in data[name]:
                    del data[name][credential_type]
            else:
                del data[name]
        self._save_store(data)
    
    def list_credentials(self) -> dict:
        """List all stored credential names"""
        data = self._load_store()
        return {name: list(creds.keys()) for name, creds in data.items()}


# Global instance
secure_store = SecureStore()
