"""
Configuration settings for the notepad scanner application.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Camera: Picamera2 is configured in camera_manager per experiments/picamera_control_references.py
# (2304x1296 main stream, then rotated 90° CW for preview/capture).
# PREVIEW_WIDTH is the width used when resizing frames for the browser preview stream.
PREVIEW_WIDTH = int(os.getenv("PREVIEW_WIDTH", "1280"))

# Fixed region of interest (ROI) for cropping captured frames.
# Format: (x, y, width, height) in pixels, or None to use full frame.
# Set via env e.g. ROI_X, ROI_Y, ROI_WIDTH, ROI_HEIGHT when you have fixed camera geometry.
ROI_X = int(os.getenv("ROI_X", "0"))
ROI_Y = int(os.getenv("ROI_Y", "0"))
ROI_WIDTH = int(os.getenv("ROI_WIDTH", "0"))   # 0 = use full frame width
ROI_HEIGHT = int(os.getenv("ROI_HEIGHT", "0"))  # 0 = use full frame height

# Preview tuning (helps on Raspberry Pi / low-power devices)
PREVIEW_JPEG_QUALITY = int(os.getenv("PREVIEW_JPEG_QUALITY", "85"))
PREVIEW_RESIZE_INTERPOLATION = os.getenv("PREVIEW_RESIZE_INTERPOLATION", "linear").lower()

# Paths
CAPTURE_OUTPUT_DIR = os.getenv("CAPTURE_OUTPUT_DIR", "data/captures")
PROMPT_PATH = "backend/prompts/handwriting_ocr.txt"
USERS_FILE = "data/users.json"
DATA_DIR = "data"

# API settings
NOTION_API_URL = "https://api.notion.com/v1"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NOTION_TOKEN = os.getenv("SPENCER_NOTION_TOKEN") or os.getenv("CELESTE_NOTION_TOKEN")

# Server settings
HOST = "127.0.0.1"
PORT = 5000
DEBUG = False
