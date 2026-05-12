"""
FRED Accounts - Lokale Profil-Verwaltung mit verschiedenen Kontext-Personas
Local Profile Management with different context personas
"""

import os
import json
from datetime import datetime

ACCOUNTS_PATH = os.path.expanduser("~/fred/accounts.json")


def get_accounts_path():
    """Get the accounts file path"""
    return ACCOUNTS_PATH


def init_accounts_file():
    """Initialize accounts file if it doesn't exist"""
    if not os.path.exists(ACCOUNTS_PATH):
        os.makedirs(os.path.dirname(ACCOUNTS_PATH), exist_ok=True)
        default_data = {
            "current_profile": "default",
            "profiles": {
                "default": {
                    "name": "Default",
                    "description": "Standard-Profil / Default Profile",
                    "created_at": str(datetime.now()),
                    "settings": {
                        "language": "de",
                        "theme": "dark",
                        "provider": "openai",
                        "model": "gpt-4o-mini"
                    },
                    "vault_enabled": False
                }
            }
        }
        with open(ACCOUNTS_PATH, 'w') as f:
            json.dump(default_data, f, indent=2)
        return True
    return False


def load_accounts() -> dict:
    """Load all accounts data"""
    init_accounts_file()
    with open(ACCOUNTS_PATH, 'r') as f:
        return json.load(f)


def save_accounts(data: dict):
    """Save accounts data"""
    with open(ACCOUNTS_PATH, 'w') as f:
        json.dump(data, f, indent=2)


def get_current_profile() -> str:
    """Get current active profile name"""
    data = load_accounts()
    return data.get("current_profile", "default")


def set_current_profile(profile_name: str) -> bool:
    """Set current active profile"""
    data = load_accounts()
    if profile_name in data["profiles"]:
        data["current_profile"] = profile_name
        save_accounts(data)
        return True
    return False


def get_profile(profile_name: str) -> dict | None:
    """Get profile data by name"""
    data = load_accounts()
    return data["profiles"].get(profile_name)


def list_profiles() -> list:
    """List all profile names"""
    data = load_accounts()
    return list(data["profiles"].keys())


def create_profile(profile_name: str, description: str = "", settings: dict = None) -> bool:
    """Create a new profile"""
    data = load_accounts()
    
    if profile_name in data["profiles"]:
        return False  # Profile already exists
    
    data["profiles"][profile_name] = {
        "name": profile_name.capitalize(),
        "description": description or f"Profil {profile_name}",
        "created_at": str(datetime.now()),
        "settings": settings or {
            "language": "de",
            "theme": "dark",
            "provider": "openai",
            "model": "gpt-4o-mini"
        },
        "vault_enabled": False
    }
    
    save_accounts(data)
    return True


def update_profile(profile_name: str, description: str = None, settings: dict = None) -> bool:
    """Update existing profile"""
    data = load_accounts()
    
    if profile_name not in data["profiles"]:
        return False
    
    if description is not None:
        data["profiles"][profile_name]["description"] = description
    
    if settings is not None:
        data["profiles"][profile_name]["settings"].update(settings)
    
    data["profiles"][profile_name]["updated_at"] = str(datetime.now())
    
    save_accounts(data)
    return True


def delete_profile(profile_name: str) -> bool:
    """Delete a profile (cannot delete default or current profile)"""
    data = load_accounts()
    
    if profile_name == "default":
        return False  # Cannot delete default profile
    
    if profile_name == data["current_profile"]:
        return False  # Cannot delete current profile
    
    if profile_name not in data["profiles"]:
        return False
    
    del data["profiles"][profile_name]
    save_accounts(data)
    return True


def get_profile_setting(profile_name: str, key: str, default=None):
    """Get a specific setting from a profile"""
    profile = get_profile(profile_name)
    if profile:
        return profile.get("settings", {}).get(key, default)
    return default


def set_profile_setting(profile_name: str, key: str, value) -> bool:
    """Set a specific setting in a profile"""
    data = load_accounts()
    
    if profile_name not in data["profiles"]:
        return False
    
    data["profiles"][profile_name]["settings"][key] = value
    data["profiles"][profile_name]["updated_at"] = str(datetime.now())
    
    save_accounts(data)
    return True


def is_vault_enabled(profile_name: str) -> bool:
    """Check if vault is enabled for a profile"""
    profile = get_profile(profile_name)
    if profile:
        return profile.get("vault_enabled", False)
    return False


def set_vault_enabled(profile_name: str, enabled: bool) -> bool:
    """Enable or disable vault for a profile"""
    data = load_accounts()
    
    if profile_name not in data["profiles"]:
        return False
    
    data["profiles"][profile_name]["vault_enabled"] = enabled
    data["profiles"][profile_name]["updated_at"] = str(datetime.now())
    
    save_accounts(data)
    return True


def switch_profile(profile_name: str) -> dict | None:
    """Switch to a different profile and return its data"""
    if set_current_profile(profile_name):
        return get_profile(profile_name)
    return None


def export_profile(profile_name: str) -> dict | None:
    """Export profile data for backup"""
    return get_profile(profile_name)


def import_profile(profile_name: str, profile_data: dict) -> bool:
    """Import profile data from backup"""
    data = load_accounts()
    
    # Ensure required fields
    if "settings" not in profile_data:
        profile_data["settings"] = {}
    if "created_at" not in profile_data:
        profile_data["created_at"] = str(datetime.now())
    
    profile_data["imported_at"] = str(datetime.now())
    
    data["profiles"][profile_name] = profile_data
    save_accounts(data)
    return True


if __name__ == "__main__":
    print("FRED Accounts Module")
    init_accounts_file()
    
    print("\nAvailable profiles:")
    for p in list_profiles():
        print(f"  - {p}")
    
    print(f"\nCurrent profile: {get_current_profile()}")
