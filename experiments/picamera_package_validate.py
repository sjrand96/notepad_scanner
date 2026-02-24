#!/usr/bin/python3

import argparse
from pathlib import Path
import time
import cv2
from picamera2 import Picamera2
from libcamera import controls

# Save every Nth frame to a subfolder. 0 = never capture.
CAPTURE_EVERY_N_FRAMES = 4


def main():
    parser = argparse.ArgumentParser(description="Picamera2 package validation with optional frame capture.")
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        default=CAPTURE_EVERY_N_FRAMES,
        help="Save every Nth frame to subfolder (default: %(default)s). 0 = never capture.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Subfolder for saved frames (default: picamera_captures next to this script).",
    )
    args = parser.parse_args()

    capture_interval = max(0, args.interval)
    out_dir = args.output_dir
    if out_dir is None:
        out_dir = Path(__file__).resolve().parent / "picamera_captures"
    out_dir = out_dir.resolve()
    if capture_interval > 0:
        out_dir.mkdir(parents=True, exist_ok=True)

    face_detector = cv2.CascadeClassifier(
        "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"
    )
    cv2.startWindowThread()
    picam2 = Picamera2()
    picam2.configure(
        picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (4608, 2592)})
    )
    picam2.start()
    picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

    frame_count = 0
    while True:
        im = picam2.capture_array()

        if capture_interval > 0 and frame_count > 0 and frame_count % capture_interval == 0:
            ts = time.strftime("%Y%m%d_%H%M%S")
            path = out_dir / f"{ts}_frame_{frame_count:06d}.png"
            # XRGB8888 is BGRX in memory (picamera2); use BGRA2BGR
            bgr = cv2.cvtColor(im, cv2.COLOR_BGRA2BGR)
            bgr = cv2.rotate(bgr, cv2.ROTATE_90_CLOCKWISE)
            cv2.imwrite(str(path), bgr)
        frame_count += 1
        time.sleep(0.25)

        # cv2.imshow("Camera", im)
        # cv2.waitKey(1)


if __name__ == "__main__":
    main()