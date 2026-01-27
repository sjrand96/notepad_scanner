# Notepad Scanner - Backend Setup & Running Instructions

## Prerequisites

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   
   Copy `.env.example` to `.env` and fill in your values:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your API keys and tokens:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   SPENCER_NOTION_TOKEN=your_spencer_notion_token_here
   SPENCER_NOTION_DATABASE_ID=your_spencer_database_id_here
   CELESTE_NOTION_TOKEN=your_celeste_notion_token_here
   CELESTE_NOTION_DATABASE_ID=your_celeste_database_id_here
   ```

3. **Create data directory:**
   
   The application will automatically create the `data/` directory and `data/users.json` file on first run with default users (Spencer and Celeste). You can edit `data/users.json` to configure each user's Notion database ID.

## Running the Application

### Option 1: Run directly with Python

From the project root directory:
```bash
python backend/app.py
```

Or:
```bash
python -m backend.app
```

### Option 2: Run with Flask (recommended for development)

```bash
export FLASK_APP=backend/app.py
export FLASK_ENV=development  # Optional: enables debug mode
flask run
```

The server will start on `http://127.0.0.1:5000`

## Accessing the Application

Once running, open your browser and navigate to:
```
http://127.0.0.1:5000
```

The web interface will be served automatically.

## Configuration

- **Server host/port:** Edit `backend/config.py` (default: `127.0.0.1:5000`)
- **User profiles:** Edit `data/users.json` after first run
- **Camera settings:** Edit `backend/config.py` (PREVIEW_WIDTH, CAPTURE_WIDTH, etc.)
- **Preview tuning (Raspberry Pi):** See [RASPBERRY_PI_TUNING.md](RASPBERRY_PI_TUNING.md) for `PREVIEW_WIDTH`, `PREVIEW_JPEG_QUALITY`, `PREVIEW_RESIZE_INTERPOLATION`, `PREVIEW_DETECT_EVERY_N`, and benchmarking.

## API Endpoints

- `GET /` - Serve web interface
- `GET /api/users` - List available users
- `POST /api/session` - Start session with user
- `GET /api/preview?session_id=<id>` - Get live camera preview. Add `&benchmark=1` for per-stage timings (see [RASPBERRY_PI_TUNING.md](RASPBERRY_PI_TUNING.md)).
- `POST /api/capture` - Capture a frame
- `POST /api/review` - Process frames and get cropped images
- `POST /api/process` - Process and upload to Notion
- `DELETE /api/session/<session_id>` - End session

## Troubleshooting

- **Camera not found:** Ensure camera is connected and accessible
- **Import errors:** Make sure you're running from the project root directory
- **Module not found:** Verify all dependencies are installed: `pip install -r requirements.txt`
