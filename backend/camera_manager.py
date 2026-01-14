"""
Camera manager singleton for handling camera access.
"""
import cv2
import threading
from backend.config import CAPTURE_WIDTH, CAPTURE_HEIGHT, PREVIEW_WIDTH


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
        self._initialized = True
    
    def initialize(self):
        """Initialize camera."""
        if self.is_initialized:
            return True
        
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            return False
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.capture_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.capture_height)
        
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        self.capture_width = actual_width
        self.capture_height = actual_height
        self.is_initialized = True
        
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
            self.cap.release()
            self.cap = None
            self.is_initialized = False
    
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
