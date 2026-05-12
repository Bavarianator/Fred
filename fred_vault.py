"""
FRED Vault - Verschlüsselter Schlüsselbund für API-Keys
Encrypted Keyring for API Keys with Fernet Encryption
"""

import os
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import hashlib

VAULT_PATH = os.path.expanduser("~/fred/vault.json")
SALT_PATH = VAULT_PATH.replace('.json', '.salt')


def derive_key(master_password: str, salt: bytes) -> bytes:
    """Derive encryption key from master password using PBKDF2"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(master_password.encode()))


def init_vault(master_password: str) -> bool:
    """Initialize vault with master password"""
    if os.path.exists(VAULT_PATH) or os.path.exists(SALT_PATH):
        return False  # Vault already exists
    
    os.makedirs(os.path.dirname(VAULT_PATH), exist_ok=True)
    
    salt = os.urandom(16)
    key = derive_key(master_password, salt)
    fernet = Fernet(key)
    
    vault_data = {
        "salt": base64.b64encode(salt).decode(),
        "entries": {}
    }
    
    encrypted_content = fernet.encrypt(json.dumps(vault_data).encode())
    
    with open(VAULT_PATH, 'wb') as f:
        f.write(encrypted_content)
    with open(SALT_PATH, 'wb') as f:
        f.write(salt)
    
    return True


def unlock_vault(master_password: str) -> dict | None:
    """Unlock vault and return decrypted data"""
    if not os.path.exists(VAULT_PATH) or not os.path.exists(SALT_PATH):
        return None
    
    with open(SALT_PATH, 'rb') as f:
        salt = f.read()
    
    key = derive_key(master_password, salt)
    fernet = Fernet(key)
    
    try:
        with open(VAULT_PATH, 'rb') as f:
            encrypted_data = f.read()
        vault_data = json.loads(fernet.decrypt(encrypted_data).decode())
        return vault_data
    except Exception:
        return None


def save_entry(master_password: str, service: str, api_key: str, description: str = "") -> bool:
    """Save an API key entry to vault"""
    if not os.path.exists(VAULT_PATH) or not os.path.exists(SALT_PATH):
        return False
    
    with open(SALT_PATH, 'rb') as f:
        salt = f.read()
    
    key = derive_key(master_password, salt)
    fernet = Fernet(key)
    
    try:
        with open(VAULT_PATH, 'rb') as f:
            encrypted_data = f.read()
        vault_data = json.loads(fernet.decrypt(encrypted_data).decode())
    except:
        vault_data = {"entries": {}}
    
    vault_data["entries"][service] = {
        "api_key": api_key,
        "description": description,
        "updated_at": str(__import__('datetime').datetime.now())
    }
    
    encrypted_content = fernet.encrypt(json.dumps(vault_data).encode())
    
    with open(VAULT_PATH, 'wb') as f:
        f.write(encrypted_content)
    
    return True


def get_entry(master_password: str, service: str) -> dict | None:
    """Retrieve an API key entry from vault"""
    if not os.path.exists(VAULT_PATH) or not os.path.exists(SALT_PATH):
        return None
    
    with open(SALT_PATH, 'rb') as f:
        salt = f.read()
    
    key = derive_key(master_password, salt)
    fernet = Fernet(key)
    
    try:
        with open(VAULT_PATH, 'rb') as f:
            encrypted_data = f.read()
        vault_data = json.loads(fernet.decrypt(encrypted_data).decode())
        return vault_data["entries"].get(service)
    except:
        return None


def delete_entry(master_password: str, service: str) -> bool:
    """Delete an API key entry from vault"""
    if not os.path.exists(VAULT_PATH) or not os.path.exists(SALT_PATH):
        return False
    
    with open(SALT_PATH, 'rb') as f:
        salt = f.read()
    
    key = derive_key(master_password, salt)
    fernet = Fernet(key)
    
    try:
        with open(VAULT_PATH, 'rb') as f:
            encrypted_data = f.read()
        vault_data = json.loads(fernet.decrypt(encrypted_data).decode())
        
        if service in vault_data["entries"]:
            del vault_data["entries"][service]
            encrypted_content = fernet.encrypt(json.dumps(vault_data).encode())
            with open(VAULT_PATH, 'wb') as f:
                f.write(encrypted_content)
            return True
    except:
        pass
    
    return False


def list_entries(master_password: str) -> list:
    """List all service names in vault"""
    if not os.path.exists(VAULT_PATH) or not os.path.exists(SALT_PATH):
        return []
    
    with open(SALT_PATH, 'rb') as f:
        salt = f.read()
    
    key = derive_key(master_password, salt)
    fernet = Fernet(key)
    
    try:
        with open(VAULT_PATH, 'rb') as f:
            encrypted_data = f.read()
        vault_data = json.loads(fernet.decrypt(encrypted_data).decode())
        return list(vault_data["entries"].keys())
    except:
        return []


def change_master_password(old_password: str, new_password: str) -> bool:
    """Change the master password"""
    if not os.path.exists(VAULT_PATH) or not os.path.exists(SALT_PATH):
        return False
    
    with open(SALT_PATH, 'rb') as f:
        salt = f.read()
    
    old_key = derive_key(old_password, salt)
    fernet_old = Fernet(old_key)
    
    try:
        with open(VAULT_PATH, 'rb') as f:
            encrypted_data = f.read()
        vault_data = json.loads(fernet_old.decrypt(encrypted_data).decode())
        
        # Generate new salt
        new_salt = os.urandom(16)
        new_key = derive_key(new_password, new_salt)
        fernet_new = Fernet(new_key)
        
        vault_data["salt"] = base64.b64encode(new_salt).decode()
        encrypted_content = fernet_new.encrypt(json.dumps(vault_data).encode())
        
        with open(VAULT_PATH, 'wb') as f:
            f.write(encrypted_content)
        with open(SALT_PATH, 'wb') as f:
            f.write(new_salt)
        
        return True
    except:
        return False


def vault_exists() -> bool:
    """Check if vault exists"""
    return os.path.exists(VAULT_PATH) and os.path.exists(SALT_PATH)


if __name__ == "__main__":
    print("FRED Vault Module")
    print("Use init_vault(password) to create a new vault")
    print("Use unlock_vault(password) to access existing vault")
