# User-Specific Token Implementation

## Summary
Updated the system to properly respect user-specific Notion tokens (SPENCER_NOTION_TOKEN and CELESTE_NOTION_TOKEN) across all workflows, including standalone scripts and the web API.

## Changes Made

### 1. `backend/config.py`
- Updated `NOTION_TOKEN` to check for both SPENCER_NOTION_TOKEN and CELESTE_NOTION_TOKEN
- Provides a fallback default token for backward compatibility

### 2. `scan_to_notion.py`
- Added `user_id` parameter to `scan_and_insert_to_notion()` function
- Imports `get_user()` from `backend.user_manager` to fetch user credentials
- Automatically uses user-specific token and database_id when `user_id` is provided
- Falls back to environment variables/defaults if no `user_id` specified

### 3. `capture_scan_to_notion.py`
- Added `select_user()` function that prompts user selection at startup
- Displays available users from `data/users.json`
- Validates that user credentials are configured
- Passes `user_id` to `process_cropped_images_to_notion()`
- Updated `process_cropped_images_to_notion()` to accept and use `user_id` parameter

### 4. `backend/app.py` (Flask Web API)
- Updated `create_page_with_bulleted_list()` call to include `image_path` parameter
- Already properly uses user-specific tokens from session (no changes needed to user flow)

### 5. `IMAGE_UPLOAD_IMPLEMENTATION.md`
- Updated documentation to reflect multi-user support
- Added environment variables section listing all required tokens

## How It Works

### User Credential Flow

```
1. Environment Variables (.env)
   ├── SPENCER_NOTION_TOKEN
   ├── SPENCER_NOTION_DATABASE_ID
   ├── CELESTE_NOTION_TOKEN
   └── CELESTE_NOTION_DATABASE_ID

2. User Manager (backend/user_manager.py)
   └── Loads credentials into data/users.json
       ├── spencer: {name, notion_token, notion_database_id}
       └── celeste: {name, notion_token, notion_database_id}

3. Workflows
   ├── Web API: User selected in UI → credentials stored in session
   ├── capture_scan_to_notion.py: Prompts user selection → uses credentials
   └── scan_to_notion.py: Accepts user_id parameter → uses credentials
```

## Usage Examples

### Standalone Script with User ID
```python
from scan_to_notion import scan_and_insert_to_notion

# Use Spencer's credentials
scan_and_insert_to_notion('image.jpg', user_id='spencer')

# Use Celeste's credentials
scan_and_insert_to_notion('image.jpg', user_id='celeste')

# Use default credentials from environment
scan_and_insert_to_notion('image.jpg')
```

### ArUco Capture Workflow
```bash
python capture_scan_to_notion.py
# Prompts:
# USER SELECTION
# 1. Spencer (spencer)
# 2. Celeste (celeste)
# 3. Skip (use default credentials)
# Select user (1-3): 
```

### Web API
No changes to API - already handled correctly through session management.

## Testing Results

✅ **Spencer's credentials** - Successfully created page in Spencer's database  
✅ **Celeste's credentials** - Successfully created page in Celeste's database  
✅ **Image upload** - Works with both users  
✅ **Backward compatibility** - Works without user_id (uses defaults)

## File Structure

```
notepad_scanner/
├── backend/
│   ├── config.py              # Default token configuration
│   ├── user_manager.py        # User credential management
│   ├── notion_client.py       # Notion API with image upload
│   └── app.py                 # Flask API (now with image upload)
├── data/
│   └── users.json             # User profiles and credentials
├── scan_to_notion.py          # Updated with user_id support
├── capture_scan_to_notion.py  # Updated with user selection prompt
└── IMAGE_UPLOAD_IMPLEMENTATION.md
```

## Environment Setup

Create a `.env` file in the project root:

```bash
# Spencer's Notion credentials
SPENCER_NOTION_TOKEN=ntn_****
SPENCER_NOTION_DATABASE_ID=****

# Celeste's Notion credentials
CELESTE_NOTION_TOKEN=ntn_****
CELESTE_NOTION_DATABASE_ID=****

# OpenAI API key (shared)
OPENAI_API_KEY=sk-****
```

## Next Steps

The system now fully supports:
- ✅ Multiple users with separate Notion accounts
- ✅ Image upload for all workflows
- ✅ User selection in standalone scripts
- ✅ User-specific tokens from environment variables
- ✅ Backward compatibility with default credentials

All workflows (web app, standalone scripts, ArUco capture) now properly respect user-specific Notion tokens!
