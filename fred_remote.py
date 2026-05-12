"""
FRED Remote - Token-basierte Remote-Authentifizierung
Token-based Remote Authentication
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta

REMOTE_PATH = os.path.expanduser("~/fred/remote_auth.json")


def get_remote_path():
    """Get the remote auth file path"""
    return REMOTE_PATH


def init_remote_file():
    """Initialize remote auth file if it doesn't exist"""
    if not os.path.exists(REMOTE_PATH):
        os.makedirs(os.path.dirname(REMOTE_PATH), exist_ok=True)
        default_data = {
            "tokens": {},
            "settings": {
                "token_expiry_hours": 24,
                "max_tokens": 10
            }
        }
        with open(REMOTE_PATH, 'w') as f:
            json.dump(default_data, f, indent=2)
        return True
    return False


def load_remote() -> dict:
    """Load remote auth data"""
    init_remote_file()
    with open(REMOTE_PATH, 'r') as f:
        return json.load(f)


def save_remote(data: dict):
    """Save remote auth data"""
    with open(REMOTE_PATH, 'w') as f:
        json.dump(data, f, indent=2)


def generate_token(client_name: str, expiry_hours: int = None) -> str:
    """Generate a new authentication token"""
    data = load_remote()
    
    if expiry_hours is None:
        expiry_hours = data["settings"].get("token_expiry_hours", 24)
    
    # Check max tokens limit
    if len(data["tokens"]) >= data["settings"].get("max_tokens", 10):
        # Remove oldest expired token
        now = datetime.now().isoformat()
        for token_id, token_data in list(data["tokens"].items()):
            if token_data.get("expires_at", "") < now:
                del data["tokens"][token_id]
                break
        
        # Still at limit?
        if len(data["tokens"]) >= data["settings"].get("max_tokens", 10):
            return None
    
    # Generate secure token
    token = secrets.token_urlsafe(32)
    token_id = hashlib.sha256(token.encode()).hexdigest()[:16]
    
    expires_at = (datetime.now() + timedelta(hours=expiry_hours)).isoformat()
    
    data["tokens"][token_id] = {
        "client_name": client_name,
        "created_at": datetime.now().isoformat(),
        "expires_at": expires_at,
        "last_used": None,
        "active": True
    }
    
    save_remote(data)
    return token


def validate_token(token: str) -> dict | None:
    """Validate a token and return token info if valid"""
    data = load_remote()
    token_id = hashlib.sha256(token.encode()).hexdigest()[:16]
    
    if token_id not in data["tokens"]:
        return None
    
    token_data = data["tokens"][token_id]
    
    if not token_data.get("active", True):
        return None
    
    if datetime.fromisoformat(token_data["expires_at"]) < datetime.now():
        return None  # Token expired
    
    # Update last used
    token_data["last_used"] = datetime.now().isoformat()
    save_remote(data)
    
    return {
        "token_id": token_id,
        "client_name": token_data["client_name"],
        "expires_at": token_data["expires_at"]
    }


def revoke_token(token: str) -> bool:
    """Revoke a token"""
    data = load_remote()
    token_id = hashlib.sha256(token.encode()).hexdigest()[:16]
    
    if token_id not in data["tokens"]:
        return False
    
    del data["tokens"][token_id]
    save_remote(data)
    return True


def revoke_all_tokens() -> bool:
    """Revoke all tokens"""
    data = load_remote()
    data["tokens"] = {}
    save_remote(data)
    return True


def list_tokens() -> list:
    """List all active tokens (without exposing the actual token values)"""
    data = load_remote()
    tokens = []
    
    now = datetime.now()
    for token_id, token_data in data["tokens"].items():
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        is_expired = expires_at < now
        
        tokens.append({
            "token_id": token_id,
            "client_name": token_data["client_name"],
            "created_at": token_data["created_at"],
            "expires_at": token_data["expires_at"],
            "last_used": token_data.get("last_used"),
            "active": token_data.get("active", True) and not is_expired,
            "is_expired": is_expired
        })
    
    return tokens


def cleanup_expired_tokens() -> int:
    """Remove all expired tokens, returns count of removed tokens"""
    data = load_remote()
    now = datetime.now().isoformat()
    
    expired = [
        token_id for token_id, token_data in data["tokens"].items()
        if token_data.get("expires_at", "") < now
    ]
    
    for token_id in expired:
        del data["tokens"][token_id]
    
    if expired:
        save_remote(data)
    
    return len(expired)


def set_token_expiry(hours: int) -> bool:
    """Set default token expiry hours"""
    data = load_remote()
    data["settings"]["token_expiry_hours"] = hours
    save_remote(data)
    return True


def set_max_tokens(max_count: int) -> bool:
    """Set maximum number of allowed tokens"""
    data = load_remote()
    data["settings"]["max_tokens"] = max(1, min(100, max_count))
    save_remote(data)
    return True


def refresh_token(token: str, additional_hours: int = 24) -> str | None:
    """Refresh an existing token with new expiry time"""
    token_info = validate_token(token)
    if not token_info:
        return None
    
    data = load_remote()
    token_id = hashlib.sha256(token.encode()).hexdigest()[:16]
    
    new_expires = (datetime.now() + timedelta(hours=additional_hours)).isoformat()
    data["tokens"][token_id]["expires_at"] = new_expires
    
    save_remote(data)
    return token


if __name__ == "__main__":
    print("FRED Remote Auth Module")
    init_remote_file()
    
    print("\nGenerating test token...")
    token = generate_token("Test Client")
    if token:
        print(f"Token: {token}")
        
        print("\nValidating token...")
        info = validate_token(token)
        if info:
            print(f"Valid! Client: {info['client_name']}")
        
        print("\nListing tokens...")
        for t in list_tokens():
            print(f"  - {t['client_name']} (ID: {t['token_id']})")