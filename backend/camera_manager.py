"""
Camera manager singleton for handling camera access.
"""
import cv2
import threading
import time
import logging
from backend.config import CAPTURE_WIDTH, CAPTURE_HEIGHT, PREVIEW_WIDTH

# Set up logger
logger = logging.getLogger('notepad_scanner')
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)


class CameraManager:
    """Singleton camera manager for thread-safe camera access."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CameraManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.cap = None
        self.is_initialized = False
        self.capture_width = CAPTURE_WIDTH
        self.capture_height = CAPTURE_HEIGHT
        self.preview_width = PREVIEW_WIDTH
        self._last_release_time = 0
        self._last_init_attempt = 0
        self._init_cooldown = 2.0  # Seconds between initialization attempts
        self._initialized = True
    
    def initialize(self, force=False):
        """Initialize camera.
        
        Args:
            force: If True, reinitialize even if already initialized
        """
        if self.is_initialized and not force:
            return True
        
        # Enforce cooldown between initialization attempts to prevent flooding
        current_time = time.time()
        time_since_last_attempt = current_time - self._last_init_attempt
        if time_since_last_attempt < self._init_cooldown and not force:
            # Too soon to retry
            return False
        
        self._last_init_attempt = current_time
        
        # If camera was recently released, wait a bit for hardware to reset
        time_since_release = current_time - self._last_release_time
        if time_since_release < 0.5:  # Wait at least 500ms after release
            time.sleep(0.5 - time_since_release)
        
        # Release existing camera if any
        if self.cap is not None:
            self.cap.release()
            time.sleep(0.1)  # Brief pause for hardware cleanup
        
        # Try to open camera with reduced verbosity
        import os
        # Suppress OpenCV warnings temporarily
        os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
        
        logger.info("📷 Initializing camera...")
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.is_initialized = False
            logger.warning("❌ Camera initialization failed")
            return False
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.capture_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.capture_height)
        
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        self.capture_width = actual_width
        self.capture_height = actual_height
        self.is_initialized = True
        
        logger.info(f"✅ Camera initialized: {actual_width}x{actual_height}")
        return True
    
    def read_frame(self):
        """Read a frame from the camera."""
        if not self.is_initialized or self.cap is None:
            return None
        
        ret, frame = self.cap.read()
        if ret:
            return frame
        return None
    
    def release(self):
        """Release camera resources."""
        if self.cap is not None:
            logger.info("🔒 Releasing camera")
            self.cap.release()
            self.cap = None
            self.is_initialized = False
            self._last_release_time = time.time()
    
    def get_preview_size(self):
        """Calculate preview dimensions maintaining aspect ratio."""
        if not self.is_initialized:
            return (PREVIEW_WIDTH, int(PREVIEW_WIDTH * 3 / 4))  # Default 4:3
        
        camera_aspect = self.capture_width / self.capture_height
        if self.capture_width >= self.capture_height:
            preview_width = self.preview_width
            preview_height = int(self.preview_width / camera_aspect)
        else:
            preview_height = self.preview_width
            preview_width = int(self.preview_width * camera_aspect)
        
        return (preview_width, preview_height)
