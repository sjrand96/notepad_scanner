#!/usr/bin/env python3
"""
Benchmark raw camera read throughput using the standard OpenCV approach.

For webcams/cameras, FPS is not reliable from get(CAP_PROP_FPS). The correct method
(LearnOpenCV, OpenCV docs) is: measure wall-clock time for N frames, then
FPS = N / elapsed_seconds. Do not time each read() individually—that can be misleading
(buffer vs blocking, kernel wait time vs user time).

A short warmup (read and discard frames) ensures we measure steady-state throughput
rather than buffer fill or cold-start.

Refs:
  https://learnopencv.com/how-to-find-frame-rate-or-frames-per-second-fps-in-opencv-python-cpp/
  https://answers.opencv.org/question/184482/measuring-cvvideocaptureread-execution-time-in-milliseconds-gives-me-incorrect-fps/

Usage:
  # No backend running. Uses OpenCV VideoCapture(0) at given resolution.
  python scripts/benchmark_camera_read.py [--width W] [--height H] [--frames N] [--warmup W]

Examples:
  python scripts/benchmark_camera_read.py --width 1920 --height 1080 --frames 120
  python scripts/benchmark_camera_read.py --width 3264 --height 2448 --frames 60 --warmup 30
"""
from __future__ import annotations

import argparse
import os
import sys
import time

try:
    import cv2
except ImportError:
    print("Install opencv-python: pip install opencv-python")
    sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Benchmark camera FPS via wall-clock time over N frames (standard OpenCV method)"
    )
    ap.add_argument("--width", type=int, default=1920, help="Frame width (default 1920)")
    ap.add_argument("--height", type=int, default=1080, help="Frame height (default 1080)")
    ap.add_argument(
        "--frames",
        type=int,
        default=120,
        help="Number of frames to capture for FPS measurement (default 120)",
    )
    ap.add_argument(
        "--warmup",
        type=int,
        default=30,
        help="Frames to read and discard before timing (default 30)",
    )
    args = ap.parse_args()

    os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Failed to open camera (device 0)")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera opened: {actual_w}x{actual_h} (requested {args.width}x{args.height})")

    # Warmup: drain initial buffer so we measure steady-state (recommended for webcams)
    print(f"Warmup: reading {args.warmup} frames (discarding)...")
    for _ in range(args.warmup):
        cap.read()
    print(f"Capturing {args.frames} frames (tight loop, wall-clock)...\n")

    # Standard method: wall-clock time for N frames, FPS = N / elapsed_seconds
    start = time.perf_counter()
    success_count = 0
    for _ in range(args.frames):
        ret, frame = cap.read()
        if ret and frame is not None:
            success_count += 1
    end = time.perf_counter()
    cap.release()

    elapsed_sec = end - start
    if success_count == 0:
        print("No successful reads")
        sys.exit(1)

    fps = success_count / elapsed_sec
    ms_per_frame = 1000.0 / fps if fps > 0 else 0

    print("Result (wall-clock over N frames, standard OpenCV method)")
    print("-" * 50)
    print(f"  Frames captured:  {success_count}/{args.frames}")
    print(f"  Elapsed (s):       {elapsed_sec:.3f}")
    print(f"  FPS:              {fps:.1f}")
    print(f"  Avg ms/frame:     {ms_per_frame:.1f}")
    print("-" * 50)
    print()
    print("Compare to device specs (e.g. 30 fps @ 1080p, 15 fps @ 3264×2448).")
    print("If FPS here is low, the limit is camera/driver/OpenCV, not the app pipeline.")


if __name__ == "__main__":
    main()
