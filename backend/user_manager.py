"""
User profile management for the notepad scanner.
"""
import json
import os
from backend.config import USERS_FILE, DATA_DIR


def ensure_data_dir():
    """Ensure data directory exists."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def load_users():
    """
    Load user profiles from JSON file.
    If file doesn't exist, create it with default users using environment variables.
    
    Returns:
        Dictionary of user profiles
    """
    ensure_data_dir()
    
    if not os.path.exists(USERS_FILE):
        # Create default users file with user-specific env vars
        default_users = {
            "spencer": {
                "name": "Spencer",
                "notion_database_id": os.getenv("SPENCER_NOTION_DATABASE_ID", ""),
                "notion_token": os.getenv("SPENCER_NOTION_TOKEN", "")
            },
            "celeste": {
                "name": "Celeste",
                "notion_database_id": os.getenv("CELESTE_NOTION_DATABASE_ID", ""),
                "notion_token": os.getenv("CELESTE_NOTION_TOKEN", "")
            }
        }
        save_users(default_users)
        return default_users
    
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
        # Update existing users with env vars if not already set
        for user_id in users:
            if user_id == "spencer":
                users[user_id]["notion_token"] = os.getenv("SPENCER_NOTION_TOKEN", users[user_id].get("notion_token", ""))
                if not users[user_id].get("notion_database_id"):
                    users[user_id]["notion_database_id"] = os.getenv("SPENCER_NOTION_DATABASE_ID", "")
            elif user_id == "celeste":
                users[user_id]["notion_token"] = os.getenv("CELESTE_NOTION_TOKEN", users[user_id].get("notion_token", ""))
                if not users[user_id].get("notion_database_id"):
                    users[user_id]["notion_database_id"] = os.getenv("CELESTE_NOTION_DATABASE_ID", "")
        return users
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading users: {e}")
        return {}


def save_users(users):
    """
    Save user profiles to JSON file.
    
    Args:
        users: Dictionary of user profiles
    """
    ensure_data_dir()
    
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    except IOError as e:
        print(f"Error saving users: {e}")


def get_user(user_id):
    """
    Get user profile by ID.
    
    Args:
        user_id: User identifier (e.g., "spencer", "celeste")
    
    Returns:
        User profile dictionary or None
    """
    users = load_users()
    return users.get(user_id)


def list_users():
    """
    List all available users.
    
    Returns:
        List of user IDs
    """
    users = load_users()
    return list(users.keys())
