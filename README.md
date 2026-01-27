## Notepad Scanner
Digitize handwritten notes into structured Notion pages using a camera, ArUco markers, and OpenAI OCR.

### What it does
- **Live camera preview** in the browser with ArUco markers to frame each page.
- **Capture & crop pages** automatically based on the markers.
- **OCR with OpenAI** using a prompt tuned for handwritten notes.
- **Create Notion pages** (with optional source image) in a per‑user Notion database.

### Prerequisites
- **Python 3.10+** (tested on Raspberry Pi and Linux)
- A **camera** accessible to OpenCV
- A **Notion integration** with access to your target database
- An **OpenAI API key**

### 1. Clone and install
```bash
git clone https://github.com/your-username/notepad_scanner.git
cd notepad_scanner
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables
Create a `.env` file in the project root (copy from `.env.example` if present) and set:

```bash
OPENAI_API_KEY=your_openai_api_key

SPENCER_NOTION_TOKEN=your_notion_integration_token
SPENCER_NOTION_DATABASE_ID=your_notion_database_id
```

You can use any ID, not just `SPENCER`; match it with `data/users.json` as described below.

### 3. Configure users
User profiles live in `data/users.json` (auto‑created on first run if missing). Each top‑level key is a **user ID** (stable identifier), and each entry must include:

```json
{
  "spencer": {
    "name": "Spencer",
    "notion_database_id": "YOUR_SPENCER_DATABASE_ID",
    "notion_token_env_var_name": "SPENCER_NOTION_TOKEN"
  }
}
```

- **`name`**: Display name shown in the UI.
- **`notion_database_id`**: Target Notion database for this user.
- **`notion_token_env_var_name`**: Name of the env var that holds this user’s Notion token.

To add another user, add another object with a new ID (e.g. `"alice"`) and set:
- `ALICE_NOTION_TOKEN` and `ALICE_NOTION_DATABASE_ID` in `.env`
- A matching entry for `"alice"` in `data/users.json` with `"notion_token_env_var_name": "ALICE_NOTION_TOKEN"`.

> **Note:** `data/users.json` is git‑ignored; API keys and tokens live only in environment variables, not in version control.

### 4. Run the backend
```bash
source venv/bin/activate  # if not already active
python -m backend.app
```

The backend starts on `http://127.0.0.1:5000` by default.

### 5. Open the frontend
Open `frontend/index.html` in a browser (or serve `frontend/` with any static file server). The UI will:
- Ask you to select a user.
- Show live camera preview with markers.
- Let you capture, review, and send pages to Notion.

### 6. Notes and troubleshooting
- If you see JSON errors about a user configuration, check `data/users.json` and your `.env` values.
- Camera performance and preview quality can be tuned via env vars documented in `backend/config.py` (e.g. `PREVIEW_JPEG_QUALITY`, `PREVIEW_RESIZE_INTERPOLATION`).
