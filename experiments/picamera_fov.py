#!/usr/bin/python3
import time
import cv2
from picamera2 import MappedArray, Picamera2, Preview

picam2 = Picamera2()
picam2.start_preview(Preview.QTGL)
config = picam2.create_preview_configuration(main={"size": (640, 480)},
                                             lores={"size": (320, 240), "format": "YUV420"})
picam2.configure(config)

(w0, h0) = picam2.stream_configuration("main")["size"]
(w1, h1) = picam2.stream_configuration("lores")["size"]
s1 = picam2.stream_configuration("lores")["stride"]

start_time = time.monotonic()
# Run for 10 seconds.
while time.monotonic() - start_time < 10:
    buffer = picam2.capture_buffer("lores")
    