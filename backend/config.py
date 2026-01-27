"""
Configuration settings for the notepad scanner application.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Camera settings
PREVIEW_WIDTH = int(os.getenv("PREVIEW_WIDTH", "640"))
CAPTURE_WIDTH = 3264
CAPTURE_HEIGHT = 2448
MARGIN_FACTOR = 0  # Margin as fraction of marker width

# Preview tuning (helps on Raspberry Pi / low-power devices)
# - PREVIEW_JPEG_QUALITY: 60-85. Lower = faster encode, smaller payload. Default 85.
PREVIEW_JPEG_QUALITY = int(os.getenv("PREVIEW_JPEG_QUALITY", "85"))
# - PREVIEW_RESIZE_INTERPOLATION: "linear" (default) or "nearest". Nearest is faster.
PREVIEW_RESIZE_INTERPOLATION = os.getenv("PREVIEW_RESIZE_INTERPOLATION", "linear").lower()
# - PREVIEW_DETECT_EVERY_N: Run ArUco every N frames (1=always). 2 or 3 reduces CPU.
PREVIEW_DETECT_EVERY_N = max(1, int(os.getenv("PREVIEW_DETECT_EVERY_N", "1")))

# Paths
CROPPED_OUTPUT_DIR = "aruco/outputs/capture_and_crop_outputs/cropped_output_images"
LABELED_OUTPUT_DIR = "aruco/outputs/capture_and_crop_outputs/labelled_whole_images"
PROMPT_PATH = "backend/prompts/handwriting_ocr.txt"
USERS_FILE = "data/users.json"
DATA_DIR = "data"

# API settings
NOTION_API_URL = "https://api.notion.com/v1"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Default Notion token - can be overridden by user-specific tokens
NOTION_TOKEN = os.getenv("SPENCER_NOTION_TOKEN") or os.getenv("CELESTE_NOTION_TOKEN")

# Server settings
HOST = "127.0.0.1"
PORT = 5000
DEBUG = False
