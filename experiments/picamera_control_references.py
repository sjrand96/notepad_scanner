#!/usr/bin/python3

import argparse
from pathlib import Path
import time
import cv2
from picamera2 import Picamera2, Preview
from libcamera import Transform, ColorSpace, controls

## Proper example for configuring the camera, need to start the null preview before configuring and launching camera
picam2 = Picamera2()
picam2.start_preview(Preview.NULL)
preview_sensor = {
    "output_size": (2304, 1296),
    "bit_depth": 10,
}
picam2.configure(
    picam2.create_preview_configuration(
        main={
            "size": (2304, 1296),        # what you actually show in the UI
            "format": "XRGB8888",       # easy for Qt/OpenCV
        },
        raw={},                         # let Picamera2 derive raw from sensor mode
        sensor=preview_sensor,
        colour_space=ColorSpace.Sycc(),
        transform=Transform(),  
    )
)

# Example of starting the camera and setting the focus mode
picam2.start()
picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

# Example of capturing frames and saving them to a directory
frame_count = 0
out_dir='/home/spencer/Documents/notepad_scanner/experiments/picamera_captures/'

while True:
    im = picam2.capture_array()
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = out_dir + f"{ts}_frame_{frame_count:06d}.png"
    # XRGB8888 is delivered as BGRX in memory (picamera2 request.py); use BGRA2BGR
    bgr = cv2.cvtColor(im, cv2.COLOR_BGRA2BGR)
    bgr = cv2.rotate(bgr, cv2.ROTATE_90_CLOCKWISE)
    cv2.imwrite(str(path), bgr)
    time.sleep(0.25)
        
if __name__ == "__main__":
    main()