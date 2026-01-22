"""
Flask backend API for notepad scanner application.
"""
import cv2
import numpy as np
import base64
import json
import threading
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import (
    CROPPED_OUTPUT_DIR, LABELED_OUTPUT_DIR, PROMPT_PATH,
    HOST, PORT, DEBUG
)
from backend.camera_manager import CameraManager
from backend.image_processor import (
    detect_aruco_live, detect_aruco_detailed, crop_to_aruco_boundaries
)
from backend.openai_client import scan_image_to_text
from backend.notion_client import create_page_with_bulleted_list
from backend.user_manager import get_user, list_users

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Configure logging to reduce noise from frequent GET requests
# Only log warnings and errors from werkzeug (Flask's HTTP logger)
logging.getLogger('werkzeug').setLevel(logging.WARNING)

# Suppress OpenCV warnings globally
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'

# Session storage (in production, use Redis or database)
sessions = {}
session_lock = threading.Lock()

# Processing state tracker to prevent camera re-init during upload
processing_sessions = set()
processing_lock = threading.Lock()

# Custom logger for important events only
logger = logging.getLogger('notepad_scanner')
logger.setLevel(logging.INFO)
# Add console handler if not already present
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def get_session(session_id):
    """Get session data."""
    with session_lock:
        return sessions.get(session_id)


def set_session(session_id, data):
    """Set session data."""
    with session_lock:
        sessions[session_id] = data


def clear_session(session_id):
    """Clear session data."""
    with session_lock:
        if session_id in sessions:
            del sessions[session_id]


def format_datetime_title():
    """Format current datetime as 'Scan MM/DD/YYYY HH:MM:SS'."""
    now = datetime.now()
    return now.strftime("Scan %m/%d/%Y %H:%M:%S")


@app.route('/')
def index():
    """Serve the main HTML file."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/users', methods=['GET'])
def api_users():
    """Get list of available users."""
    users = list_users()
    user_list = []
    for user_id in users:
        user_data = get_user(user_id)
        if user_data:
            user_list.append({
                "id": user_id,
                "name": user_data.get("name", user_id)
            })
    return jsonify({"users": user_list})


@app.route('/api/session', methods=['POST'])
def api_start_session():
    """Start a new session with selected user."""
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    
    user = get_user(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    
    notion_token = user.get("notion_token")
    notion_database_id = user.get("notion_database_id")
    
    if not notion_token:
        return jsonify({"error": f"Notion token not configured for user {user_id}"}), 400
    if not notion_database_id:
        return jsonify({"error": f"Notion database ID not configured for user {user_id}"}), 400
    
    session_data = {
        "user_id": user_id,
        "user_name": user.get("name"),
        "notion_database_id": notion_database_id,
        "notion_token": notion_token,
        "captured_frames": [],
        "cropped_images": []
    }
    
    set_session(session_id, session_data)
    
    # Initialize camera
    camera = CameraManager()
    if not camera.initialize():
        logger.warning("Camera initialization failed on session start")
        return jsonify({"error": "Failed to initialize camera"}), 500
    
    logger.info(f"Session started for user {user.get('name')}")
    return jsonify({"session_id": session_id, "user": user})


@app.route('/api/preview', methods=['GET'])
def api_preview():
    """Get live camera preview frame."""
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({"error": "session_id required"}), 400
    
    # Don't try to use camera if session is being processed
    with processing_lock:
        if session_id in processing_sessions:
            return jsonify({"error": "Processing in progress", "code": "PROCESSING"}), 503
    
    camera = CameraManager()
    
    # Try to initialize camera if needed (with cooldown to prevent flooding)
    if not camera.is_initialized:
        # Try to initialize, but fail fast if it doesn't work
        # Cooldown is enforced in camera.initialize()
        if not camera.initialize():
            # Return error without logging - frontend will handle
            return jsonify({"error": "Camera not available", "code": "CAMERA_NOT_READY"}), 503
    
    frame = camera.read_frame()
    if frame is None:
        # Camera was initialized but can't read - may need re-init
        camera.is_initialized = False
        return jsonify({"error": "Failed to read frame", "code": "CAMERA_READ_FAILED"}), 503
    
    # Resize for preview
    preview_width, preview_height = camera.get_preview_size()
    preview_frame = cv2.resize(frame, (preview_width, preview_height))
    
    # Detect ArUco markers (lightweight)
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    try:
        aruco_params = cv2.aruco.DetectorParameters()
    except AttributeError:
        aruco_params = cv2.aruco.DetectorParameters_create()
    
    corners, ids, annotated_frame = detect_aruco_live(preview_frame, aruco_dict, aruco_params)
    
    # Encode as JPEG
    _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    jpg_base64 = base64.b64encode(buffer).decode('utf-8')
    
    marker_count = len(ids) if ids is not None else 0
    
    return jsonify({
        "image": f"data:image/jpeg;base64,{jpg_base64}",
        "marker_count": marker_count
    })


@app.route('/api/capture', methods=['POST'])
def api_capture():
    """Capture a frame and add to session."""
    data = request.json
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({"error": "session_id required"}), 400
    
    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    camera = CameraManager()
    frame = camera.read_frame()
    if frame is None:
        return jsonify({"error": "Failed to capture frame"}), 500
    
    # Store frame as base64 for now (in production, store on disk or in memory efficiently)
    _, buffer = cv2.imencode('.jpg', frame)
    frame_bytes = buffer.tobytes()
    
    session["captured_frames"].append(frame_bytes)
    set_session(session_id, session)
    
    logger.info(f"📸 Captured page {len(session['captured_frames'])}")
    
    return jsonify({
        "success": True,
        "page_count": len(session["captured_frames"])
    })


@app.route('/api/review', methods=['POST'])
def api_review():
    """Process captured frames and return cropped images for review."""
    data = request.json
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({"error": "session_id required"}), 400
    
    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    if len(session["captured_frames"]) == 0:
        return jsonify({"error": "No frames captured"}), 400
    
    # Process frames
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    try:
        aruco_params = cv2.aruco.DetectorParameters()
    except AttributeError:
        aruco_params = cv2.aruco.DetectorParameters_create()
    
    cropped_images_base64 = []
    
    for frame_bytes in session["captured_frames"]:
        # Decode frame
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            cropped_images_base64.append(None)
            continue
        
        try:
            corners, ids, labeled_image, all_corners = detect_aruco_detailed(
                frame, aruco_dict, aruco_params
            )
            
            if ids is not None and len(ids) >= 4:
                cropped = crop_to_aruco_boundaries(frame, corners, ids, 0)
                
                if cropped is not None and cropped.size > 0:
                    # Convert to RGB and encode
                    cropped_rgb = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
                    _, buffer = cv2.imencode('.jpg', cv2.cvtColor(cropped_rgb, cv2.COLOR_RGB2BGR), 
                                            [cv2.IMWRITE_JPEG_QUALITY, 90])
                    jpg_base64 = base64.b64encode(buffer).decode('utf-8')
                    cropped_images_base64.append(f"data:image/jpeg;base64,{jpg_base64}")
                else:
                    cropped_images_base64.append(None)
            else:
                cropped_images_base64.append(None)
        except Exception as e:
            logger.warning(f"Error processing frame: {e}")
            cropped_images_base64.append(None)
    
    session["cropped_images"] = cropped_images_base64
    set_session(session_id, session)
    
    return jsonify({
        "images": cropped_images_base64,
        "page_count": len(cropped_images_base64)
    })


@app.route('/api/process', methods=['POST'])
def api_process():
    """Process all cropped images and upload to Notion."""
    data = request.json
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({"error": "session_id required"}), 400
    
    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    # Mark session as processing to prevent camera re-init
    with processing_lock:
        processing_sessions.add(session_id)
    
    try:
        database_id = session.get("notion_database_id")
        if not database_id:
            return jsonify({"error": "Notion database ID not configured for user"}), 400
        
        notion_token = session.get("notion_token")
        if not notion_token:
            return jsonify({"error": "Notion token not configured for user"}), 400
        
        cropped_images = session.get("cropped_images", [])
        if len(cropped_images) == 0:
            return jsonify({"error": "No images to process"}), 400
        
        # Release camera before starting processing
        camera = CameraManager()
        camera.release()
        
        logger.info(f"🚀 Starting processing of {len(cropped_images)} page(s)")
        
        # Ensure output directories exist
        os.makedirs(CROPPED_OUTPUT_DIR, exist_ok=True)
        
        results = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for idx, img_base64 in enumerate(cropped_images):
            if img_base64 is None:
                error_msg = "Invalid image"
                logger.error(f"❌ Page {idx + 1}: {error_msg}")
                results.append({"success": False, "error": error_msg})
                continue
            
            try:
                # Decode base64 image
                header, encoded = img_base64.split(',', 1)
                image_data = base64.b64decode(encoded)
                nparr = np.frombuffer(image_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if img is None:
                    raise ValueError("Failed to decode image")
                
                # Save cropped image
                output_path = os.path.join(CROPPED_OUTPUT_DIR, f"aruco_cropped_{timestamp}_p{idx+1}.jpg")
                cv2.imwrite(output_path, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                
                # Scan with OpenAI
                logger.info(f"🤖 Page {idx + 1}/{len(cropped_images)}: Scanning with OpenAI...")
                bulleted_text = scan_image_to_text(output_path, PROMPT_PATH)
                
                # Create Notion page with image
                page_title = format_datetime_title()
                logger.info(f"📤 Page {idx + 1}/{len(cropped_images)}: Uploading to Notion...")
                result = create_page_with_bulleted_list(
                    database_id=database_id,
                    title=page_title,
                    bulleted_text=bulleted_text,
                    notion_token=notion_token,
                    image_path=output_path
                )
                logger.info(f"✅ Page {idx + 1}/{len(cropped_images)}: Upload complete")
                
                results.append({
                    "success": True,
                    "page_number": idx + 1,
                    "notion_page_id": result.get("id")
                })
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                logger.error(f"❌ Page {idx + 1}/{len(cropped_images)}: {error_msg}", exc_info=True)
                results.append({
                    "success": False,
                    "page_number": idx + 1,
                    "error": error_msg
                })
        
        # Clear session after processing
        clear_session(session_id)
        
        success_count = sum(1 for r in results if r.get("success"))
        logger.info(f"🎉 Processing complete: {success_count}/{len(results)} successful")
        
        return jsonify({
            "results": results,
            "success_count": success_count,
            "total_count": len(results)
        })
    finally:
        # Remove from processing sessions
        with processing_lock:
            processing_sessions.discard(session_id)


@app.route('/api/session/<session_id>', methods=['DELETE'])
def api_end_session(session_id):
    """End a session and release resources."""
    session = get_session(session_id)
    if session:
        clear_session(session_id)
    
    # Remove from processing sessions if present
    with processing_lock:
        processing_sessions.discard(session_id)
    
    camera = CameraManager()
    camera.release()
    
    logger.info("🔚 Session ended")
    return jsonify({"success": True})


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files (CSS, JS, etc.). Must be last to not intercept API routes."""
    return send_from_directory(app.static_folder, path)


if __name__ == '__main__':
    # Ensure output directories exist
    os.makedirs(CROPPED_OUTPUT_DIR, exist_ok=True)
    os.makedirs(LABELED_OUTPUT_DIR, exist_ok=True)
    
    app.run(host=HOST, port=PORT, debug=DEBUG)
