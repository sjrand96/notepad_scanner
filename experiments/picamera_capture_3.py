import time

from picamera2 import Picamera2, Preview
from libcamera import Transform, ColorSpace, controls

picam2 = Picamera2()

# Start preview BEFORE configure (required by picamera2 API)
picam2.start_preview(Preview.QTGL)

# --- Preview configuration: Mode 2 (2304x1296, full FOV) ---
preview_sensor = {
    "output_size": (2304, 1296),
    "bit_depth": 10,
}

preview_config = picam2.create_preview_configuration(
    main={
        "size": (1280, 720),        # what you actually show in the UI
        "format": "XRGB8888",       # easy for Qt/OpenCV
    },
    raw={},                         # let Picamera2 derive raw from sensor mode
    sensor=preview_sensor,
    colour_space=ColorSpace.Sycc(),
    transform=Transform(vflip=True, transpose=True),  # 90° clockwise   
)

print('rotating!')
picam2.configure(preview_config)
picam2.start()
picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

# Keep preview visible (otherwise script exits immediately)
time.sleep(20)
picam2.stop()