"""
User profile management for the notepad scanner.
"""
import json
import os
from backend.config import USERS_FILE, DATA_DIR


def _attach_tokens_and_ids(users):
    """
    Enrich user dictionaries with runtime-only fields derived from env vars,
    while enforcing a clear, explicit schema for users.json.

    Requirements for each user entry in users.json:
    - Must have a non-empty "notion_database_id"
    - Must have a non-empty "notion_token_env_var_name"

    At runtime:
    - If "notion_token" is already present (e.g., in tests), it is preserved.
    - Otherwise, "notion_token" is resolved from the environment variable
      whose name is given by "notion_token_env_var_name".
    """
    for user_id, user in users.items():
        id_str = str(user_id)

        # Validate presence of required fields
        db_id = user.get("notion_database_id")
        if not db_id:
            raise ValueError(
                f"User '{id_str}' is missing a non-empty 'notion_database_id' in users.json. "
                f"Please set it in data/users.json."
            )

        env_var_name = user.get("notion_token_env_var_name")
        if not env_var_name:
            raise ValueError(
                f"User '{id_str}' is missing a non-empty 'notion_token_env_var_name' in users.json. "
                f"Example: \"notion_token_env_var_name\": \"SPENCER_NOTION_TOKEN\""
            )

        # Only resolve from env if notion_token isn't already present.
        if not user.get("notion_token"):
            user["notion_token"] = os.getenv(env_var_name, "")

    return users


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
        # Create default users file with user-specific env var references.
        # We intentionally do NOT persist raw tokens here; instead we store
        # the env var name (`notion_token_env_var_name`) and resolve the token at runtime.
        default_users = {
            "spencer": {
                "name": "Spencer",
                "notion_database_id": os.getenv("SPENCER_NOTION_DATABASE_ID", ""),
                "notion_token_env_var_name": "SPENCER_NOTION_TOKEN",
            },
            "celeste": {
                "name": "Celeste",
                "notion_database_id": os.getenv("CELESTE_NOTION_DATABASE_ID", ""),
                "notion_token_env_var_name": "CELESTE_NOTION_TOKEN",
            },
        }
        save_users(default_users)
        # Enrich with runtime-only fields before returning
        return _attach_tokens_and_ids(default_users)
    
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)

        # Enrich users with runtime-only fields derived from env vars.
        # This keeps existing JSON-compatible structures (including older
        # files that already contain `notion_token`), while allowing newer
        # configs to specify `notion_token_env` and rely solely on env vars
        # for secrets.
        return _attach_tokens_and_ids(users)
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
