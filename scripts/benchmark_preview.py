#!/usr/bin/env python3
"""
Benchmark the /api/preview pipeline (read, resize, detect, encode, base64).

Usage:
  # Server must be running (e.g. python -m backend.app)
  python scripts/benchmark_preview.py [--url BASE_URL] [--samples N]

Example:
  PREVIEW_WIDTH=320 PREVIEW_JPEG_QUALITY=70 python scripts/benchmark_preview.py --samples 20
"""
from __future__ import annotations

import argparse
import statistics
import sys

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser(description="Benchmark /api/preview")
    ap.add_argument("--url", default="http://127.0.0.1:5000", help="API base URL")
    ap.add_argument("--samples", type=int, default=20, help="Number of preview requests")
    args = ap.parse_args()
    base = args.url.rstrip("/")
    n = args.samples

    # Get users and start session
    r = requests.get(f"{base}/api/users", timeout=5)
    r.raise_for_status()
    users = r.json().get("users", [])
    if not users:
        print("No users configured. Create a session manually or add users.")
        sys.exit(1)
    user_id = users[0]["id"]

    r = requests.post(
        f"{base}/api/session",
        json={"user_id": user_id},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    if not r.ok:
        print(f"Session start failed: {r.status_code} {r.text[:200]}")
        sys.exit(1)
    session_id = r.json()["session_id"]
    print(f"Session started: {session_id} (user={user_id})")
    print(f"Running {n} preview requests with benchmark=1 ...\n")

    benches = []
    for i in range(n):
        r = requests.get(
            f"{base}/api/preview",
            params={"session_id": session_id, "benchmark": "1"},
            timeout=30,
        )
        if not r.ok:
            print(f"Preview request {i+1} failed: {r.status_code} {r.text[:200]}")
            continue
        data = r.json()
        b = data.get("benchmark")
        if not b:
            print(f"Preview {i+1}: no benchmark data (ensure ?benchmark=1)")
            continue
        benches.append(b)

    # End session
    requests.delete(f"{base}/api/session/{session_id}", timeout=5)

    if not benches:
        print("No benchmark data collected.")
        sys.exit(1)

    # Aggregate
    keys = ["read_ms", "resize_ms", "detect_ms", "encode_ms", "base64_ms", "total_ms"]
    stats = {}
    for k in keys:
        vals = [b[k] for b in benches if k in b and b[k] is not None]
        if vals:
            stats[k] = {
                "min": min(vals),
                "max": max(vals),
                "avg": statistics.mean(vals),
                "median": statistics.median(vals),
            }
    total_avg = stats.get("total_ms", {}).get("avg")
    fps = 1000.0 / total_avg if total_avg and total_avg > 0 else 0
    skipped = sum(1 for b in benches if b.get("detect_skipped"))

    print("Stage timings (ms)")
    print("-" * 50)
    for k in keys:
        s = stats.get(k)
        if not s:
            continue
        print(f"  {k:12}  min={s['min']:6.1f}  max={s['max']:6.1f}  avg={s['avg']:6.1f}  median={s['median']:6.1f}")
    print("-" * 50)
    print(f"  Implied FPS (1000 / avg total_ms): {fps:.1f}")
    if skipped:
        print(f"  Detect skipped (PREVIEW_DETECT_EVERY_N): {skipped}/{n} requests")
    print()


if __name__ == "__main__":
    main()

