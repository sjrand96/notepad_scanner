#!/usr/bin/env python3
"""
ROI corner picker: select 4 corners on a preview image to get ROI_X, ROI_Y, ROI_WIDTH, ROI_HEIGHT.

Use these values in .env so the app crops captured frames to this rectangle before OCR.

Two-step workflow (for running over SSH without a display):

  1. On the Pi (over SSH): capture a frame to a file (no GUI):
       python experiments/roi_picker.py --capture
       python experiments/roi_picker.py --capture -o /path/to/frame.png

  2. Copy the image to your local machine, then run the picker locally (GUI):
       scp pi:.../notepad_scanner/experiments/roi_preview.png .
       python experiments/roi_picker.py roi_preview.png

If you get "null window handler" with OpenCV, use the matplotlib backend:
       python experiments/roi_picker.py roi_preview.png --matplotlib

Click 4 corners in any order. Press 'r' to clear, 'q' or ESC to quit (then env vars are printed).
"""

import argparse
import sys
from pathlib import Path

# Add project root for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import cv2
import numpy as np


def capture_one_frame():
    """Capture a single frame using Picamera2 (same config as camera_manager)."""
    try:
        from picamera2 import Picamera2, Preview
        from libcamera import Transform, ColorSpace, controls
    except ImportError:
        print("Picamera2 not available. Use an image file: python experiments/roi_picker.py <image.png>")
        return None

    picam2 = Picamera2()
    picam2.start_preview(Preview.NULL)
    preview_sensor = {"output_size": (2304, 1296), "bit_depth": 10}
    picam2.configure(
        picam2.create_preview_configuration(
            main={"size": (2304, 1296), "format": "XRGB8888"},
            raw={},
            sensor=preview_sensor,
            colour_space=ColorSpace.Sycc(),
            transform=Transform(),
        )
    )
    picam2.start()
    picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

    im = picam2.capture_array()
    picam2.stop()
    # XRGB8888 is delivered as BGRX in memory (picamera2); use BGRA2BGR for correct colors
    bgr = cv2.cvtColor(im, cv2.COLOR_BGRA2BGR)
    bgr = cv2.rotate(bgr, cv2.ROTATE_90_CLOCKWISE)
    return bgr


def corners_to_roi(points, img_width, img_height):
    """
    Convert 4 corner points to (roi_x, roi_y, roi_width, roi_height) bounding box.
    Clamps to image bounds and validates.
    """
    if len(points) < 4:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    roi_x = max(0, int(min(xs)))
    roi_y = max(0, int(min(ys)))
    x2 = min(img_width, int(max(xs)))
    y2 = min(img_height, int(max(ys)))
    roi_width = max(0, x2 - roi_x)
    roi_height = max(0, y2 - roi_y)
    if roi_width == 0 or roi_height == 0:
        return None
    return (roi_x, roi_y, roi_width, roi_height)


def _print_roi_env(roi):
    """Print ROI as .env lines."""
    if roi is None:
        print("ROI invalid (zero area or out of bounds).")
        return
    roi_x, roi_y, roi_width, roi_height = roi
    print()
    print("# Add these to your .env (region of interest for cropping captured frames)")
    print(f"ROI_X={roi_x}")
    print(f"ROI_Y={roi_y}")
    print(f"ROI_WIDTH={roi_width}")
    print(f"ROI_HEIGHT={roi_height}")
    print()
    print("# One line for copy-paste:")
    print(f"ROI_X={roi_x} ROI_Y={roi_y} ROI_WIDTH={roi_width} ROI_HEIGHT={roi_height}")


def _run_matplotlib_picker(img, w, h):
    """Use matplotlib to collect 4 clicks; no OpenCV highgui."""
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    fig, ax = plt.subplots()
    ax.imshow(rgb, extent=[0, w, h, 0])  # x: 0..w, y: h..0 so top-left is (0,0)
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.set_aspect("equal")
    plt.title("Click 4 corners (any order)")
    plt.tight_layout()
    clicks = plt.ginput(4, timeout=0, show_clicks=True)  # blocks until 4 clicks
    plt.close()
    if len(clicks) != 4:
        print("Need exactly 4 clicks.")
        return 1
    points = [
        (max(0, min(w - 1, int(round(x)))), max(0, min(h - 1, int(round(y)))))
        for x, y in clicks
    ]
    roi = corners_to_roi(points, w, h)
    _print_roi_env(roi)
    return 0


def _run_opencv_picker(img, w, h, display_scale):
    """Use OpenCV window and mouse callback for 4-corner selection."""


def main():
    default_output = Path(__file__).resolve().parent / "roi_preview.png"
    parser = argparse.ArgumentParser(
        description="Select 4 corners on an image to get ROI env vars for .env"
    )
    parser.add_argument(
        "image",
        nargs="?",
        type=Path,
        default=None,
        help="Path to preview image (1296x2304). Use this on your local machine after copying a frame from the Pi.",
    )
    parser.add_argument(
        "--capture",
        action="store_true",
        help="On Pi over SSH: capture one frame and save to file, then exit (no GUI). Copy the file and run with the image path locally.",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=default_output,
        help="Where to save the frame when using --capture (default: experiments/roi_preview.png).",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Scale factor for display (e.g. 0.5 to show half-size). ROI coordinates are in original pixel coords.",
    )
    parser.add_argument(
        "--matplotlib",
        action="store_true",
        help="Use matplotlib for point selection (avoids OpenCV null window on some systems). Click 4 corners in the figure.",
    )
    args = parser.parse_args()

    if args.capture:
        # Pi over SSH: capture and save only, no GUI
        print("Capturing one frame from Picamera2...")
        img = capture_one_frame()
        if img is None:
            return 1
        out_path = args.output.resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), img)
        print(f"Saved to {out_path}")
        print()
        print("Copy that file to your local machine, then run the picker locally (GUI):")
        print(f"  python experiments/roi_picker.py <path/to/copied/image>")
        return 0

    if args.image is not None:
        path = args.image.resolve()
        if not path.exists():
            print(f"File not found: {path}")
            return 1
        img = cv2.imread(str(path))
        if img is None:
            print(f"Could not load image: {path}")
            return 1
    else:
        print("No image file given and not using --capture.")
        print("On the Pi (over SSH), run:  python experiments/roi_picker.py --capture")
        print("Then copy the saved image and run:  python experiments/roi_picker.py <path/to/image>")
        return 1

    h, w = img.shape[:2]

    # Matplotlib path: avoids OpenCV highgui / null window handler on macOS and some backends
    if args.matplotlib:
        return _run_matplotlib_picker(img, w, h)

    return _run_opencv_picker(img, w, h, args.scale)


def _run_opencv_picker(img, w, h, display_scale):
    """Use OpenCV window and mouse callback for 4-corner selection."""
    points = []
    window_name = "roi_picker"

    try:
        cv2.startWindowThread()
    except Exception:
        pass

    def on_mouse(event, x, y, _flags, _param):
        nonlocal points
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        ix = int(round(x / display_scale))
        iy = int(round(y / display_scale))
        ix = max(0, min(w - 1, ix))
        iy = max(0, min(h - 1, iy))
        points.append((ix, iy))
        if len(points) > 4:
            points = points[-4:]

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    initial = img.copy()
    if display_scale != 1.0:
        initial = cv2.resize(initial, None, fx=display_scale, fy=display_scale, interpolation=cv2.INTER_AREA)
    cv2.imshow(window_name, initial)
    callback_set = False

    while True:
        if not callback_set:
            for _ in range(15):
                if cv2.waitKey(30) >= 0:
                    break
            try:
                cv2.setMouseCallback(window_name, on_mouse)
                callback_set = True
            except Exception as e:
                print(f"OpenCV mouse callback failed: {e}")
                print("Try:  python experiments/roi_picker.py <image> --matplotlib")
                callback_set = True

        vis = img.copy()
        for i, pt in enumerate(points):
            cv2.circle(vis, pt, 8, (0, 255, 0), 2)
            cv2.putText(vis, str(i + 1), (pt[0] + 10, pt[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        roi = corners_to_roi(points, w, h) if len(points) >= 4 else None
        if roi is not None:
            rx, ry, rw, rh = roi
            cv2.rectangle(vis, (rx, ry), (rx + rw, ry + rh), (0, 255, 255), 2)
            cv2.putText(vis, "ROI (4 points set)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        if display_scale != 1.0:
            vis = cv2.resize(vis, None, fx=display_scale, fy=display_scale, interpolation=cv2.INTER_AREA)
        cv2.imshow(window_name, vis)

        key = cv2.waitKey(50) & 0xFF
        if key == ord("q") or key == 27:
            break
        if key == ord("r"):
            points.clear()

    cv2.destroyAllWindows()

    if len(points) >= 4:
        _print_roi_env(corners_to_roi(points, w, h))
    else:
        print("Need at least 4 corner points.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
