"""
Camera manager singleton using Picamera2.

Configuration follows experiments/picamera_control_references.py exactly:
- Start NULL preview before configure (required by picamera2 API).
- Single preview stream 2304x1296, XRGB8888, Sycc colour space.
- Continuous autofocus after start.
- Frames from capture_array() are RGB; we convert to BGR and rotate 90° CW
  for consistency with the reference (saved frames are rotated the same way).
"""
import cv2
import threading
import time
import logging

from backend.config import PREVIEW_WIDTH

logger = logging.getLogger("notepad_scanner")
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)

# Picamera2 and libcamera are used only here; import at runtime so non-Pi envs can still load the app
def _picamera2_available():
    try:
        from picamera2 import Picamera2  # noqa: F401
        from libcamera import Transform, ColorSpace, controls  # noqa: F401
        return True
    except Exception:
        return False


class CameraManager:
    """Singleton camera manager using Picamera2 (configured per picamera_control_references.py)."""

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
        if getattr(self, "_initialized", False):
            return
        self.picam2 = None
        self.is_initialized = False
        # After ROTATE_90_CW, frame shape is (height=2304, width=1296)
        self.capture_width = 1296
        self.capture_height = 2304
        self.preview_width = PREVIEW_WIDTH
        self._last_release_time = 0
        self._last_init_attempt = 0
        self._init_cooldown = 2.0
        self._read_lock = threading.Lock()
        self._initialized = True

    def initialize(self, force=False):
        """Initialize camera using the exact sequence from picamera_control_references.py."""
        if self.is_initialized and not force:
            return True

        if not _picamera2_available():
            logger.warning("Picamera2 / libcamera not available (run on Raspberry Pi with picamera2 installed)")
            return False

        current_time = time.time()
        if current_time - self._last_init_attempt < self._init_cooldown and not force:
            return False
        self._last_init_attempt = current_time

        time_since_release = current_time - self._last_release_time
        if time_since_release < 0.5:
            time.sleep(0.5 - time_since_release)

        if self.picam2 is not None:
            try:
                self.picam2.stop()
                self.picam2.close()
            except Exception:
                pass
            self.picam2 = None
            time.sleep(0.5)

        from picamera2 import Picamera2, Preview
        from libcamera import Transform, ColorSpace, controls

        logger.info("📷 Initializing camera (Picamera2)...")

        try:
            self.picam2 = Picamera2()

            # Required: start NULL preview before configure (per reference)
            self.picam2.start_preview(Preview.NULL)

            preview_sensor = {
                "output_size": (2304, 1296),
                "bit_depth": 10,
            }
            self.picam2.configure(
                self.picam2.create_preview_configuration(
                    main={
                        "size": (2304, 1296),
                        "format": "XRGB8888",
                    },
                    raw={},
                    sensor=preview_sensor,
                    colour_space=ColorSpace.Sycc(),
                    transform=Transform(),
                )
            )

            self.picam2.start()
            self.picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

            self.is_initialized = True
            logger.info("✅ Camera initialized: 2304x1296 (Picamera2)")
            return True
        except Exception as e:
            logger.warning("❌ Camera initialization failed: %s", e)
            self.is_initialized = False
            if self.picam2 is not None:
                try:
                    self.picam2.stop()
                    self.picam2.close()
                except Exception:
                    pass
                self.picam2 = None
            return False

    def read_frame(self):
        """Capture one frame: capture_array (RGB), convert to BGR, rotate 90° CW (per reference)."""
        with self._read_lock:
            if not self.is_initialized or self.picam2 is None:
                return None
            try:
                im = self.picam2.capture_array()
                if im is None or im.size == 0:
                    return None
                bgr = cv2.cvtColor(im, cv2.COLOR_RGB2BGR)
                bgr = cv2.rotate(bgr, cv2.ROTATE_90_CLOCKWISE)
                return bgr
            except Exception as e:
                logger.warning("read_frame failed: %s", e)
                return None

    def release(self):
        """Stop camera and release resources. Must call close() so libcamera returns to Available state for next init."""
        with self._read_lock:
            if self.picam2 is not None:
                logger.info("🔒 Releasing camera")
                try:
                    self.picam2.stop()
                    self.picam2.close()
                    logger.info("Camera closed")
                except Exception as e:
                    logger.warning("Release error: %s", e)
                self.picam2 = None
                self.is_initialized = False
                self._last_release_time = time.time()

    def get_preview_size(self):
        """Return (width, height) for resizing the frame for browser preview (aspect from rotated 1296x2304)."""
        if not self.is_initialized:
            return (PREVIEW_WIDTH, int(PREVIEW_WIDTH * self.capture_height / self.capture_width))
        aspect = self.capture_height / self.capture_width  # 2304/1296
        preview_height = int(self.preview_width * aspect)
        return (self.preview_width, preview_height)
