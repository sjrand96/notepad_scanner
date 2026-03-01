## Notepad Scanner
Digitize handwritten notes into structured Notion pages using a camera, fixed region-of-interest (ROI) cropping, and OpenAI OCR. Check out the [mechanical design here](https://cad.onshape.com/documents/2dccceb40c9f25dfbf089341/w/77e00496bb0a790e8d9f75f8/e/93fd1e98c86f5fa74ec21941?renderMode=0&uiState=69a39364a531c03fedf90b3d).

### What it does
- **Live camera preview** in the browser.
- **Capture & crop pages** to a fixed region of interest (camera is fixed; ROI is configurable).
- **OCR with OpenAI** using a prompt tuned for handwritten notes.
- **Create Notion pages** (with optional source image) in a per‑user Notion database.

### Prerequisites
- **Python 3.10+** (tested on Raspberry Pi and Linux)
- A **camera** (OpenCV for now; picamera2 integration planned)
- A **Notion integration** with access to your target database
- An **OpenAI API key**

### 0. Install a fresh version of Rasperry Pi using the Pi Imager
I used the reccomended Rasperry Pi OS (64-Bit) 2025-12-04 release.

### 1. Clone the repository
```bash
git clone https://github.com/sjrand96/notepad_scanner.git
cd notepad_scanner
```

### 2. Install APT items first! This is key to the success of getting a working stack with picamera2 and opencv on the pi.
https://pip-assets.raspberrypi.com/categories/652-raspberry-pi-camera-module-2/documents/RP-008156-DS-2-picamera2-manual.pdf?disposition=inline

```bash
sudo apt update
sudo apt full-upgrade
sudo apt install -y python3-picamera2
sudo apt install -y python3-opencv
sudo apt install -y opencv-data
```

### 3. Set up Python stuff
**Make sure to cd to the project directory first**

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Optional
```

### 4. Configure environment variables
Create a `.env` file in the project root (copy from `.env.example` if present) and set:

```bash
OPENAI_API_KEY=your_openai_api_key

SPENCER_NOTION_TOKEN=your_notion_integration_token
SPENCER_NOTION_DATABASE_ID=your_notion_database_id
```

You can use any ID, not just `SPENCER`; match it with `data/users.json` as described below.

### 5. Configure users
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

### 6. Run the project
From the project directory:

```bash
./launch_kiosk.sh
```

This starts the Flask backend and opens the app in your default browser. Make sure to enter full screen within chrome to get the UI to display properly (F11 to enter/exit). Press **Ctrl+C** in the terminal when you’re done to stop the server.

### 7. Notes and troubleshooting
- If you see JSON errors about a user configuration, check `data/users.json` and your `.env` values.
- Camera performance and preview quality can be tuned via env vars documented in `backend/config.py` (e.g. `PREVIEW_JPEG_QUALITY`, `PREVIEW_RESIZE_INTERPOLATION`).
