# Raspberry Pi Preview Tuning & Benchmarking

Preview runs at ~2–3 FPS on a Raspberry Pi 5. This doc explains how to **benchmark** the pipeline, **identify bottlenecks**, and **tune config** to improve FPS.

---

## 1. Benchmarking

### Quick benchmark (single request)

With the app running and a preview session active:

```bash
# Replace SESSION_ID with a real session ID from the UI (start a session first)
curl -s "http://127.0.0.1:5000/api/preview?session_id=SESSION_ID&benchmark=1" | python3 -c "
import sys, json
d = json.load(sys.stdin)
b = d.get('benchmark', {})
if b:
    for k, v in b.items():
        if k != 'detect_skipped' and isinstance(v, (int, float)):
            print(f'  {k}: {v} ms')
    t = b.get('total_ms', 0)
    print(f'  FPS: {1000/t:.1f}' if t else '')
else:
    print('No benchmark data; check session_id and that preview is working.')
"
```

### Full benchmark script (recommended)

The `scripts/benchmark_preview.py` script runs many requests and reports min/max/avg per stage:

```bash
# Terminal 1: start the app
cd /path/to/notepad_scanner
source notebook_scanner_venv/bin/activate  # or your venv
python -m backend.app

# Terminal 2: run benchmark (default 20 samples)
python scripts/benchmark_preview.py

# Custom base URL and sample count
python scripts/benchmark_preview.py --url http://192.168.1.5:5000 --samples 30
```

Example output:

```
Session started: 20250126_120000_123456 (user=spencer)
Running 20 preview requests with benchmark=1 ...

Stage timings (ms)
--------------------------------------------------
  read_ms       min=  45.2  max=  89.1  avg=  62.3  median=  58.0
  resize_ms     min=  12.1  max=  28.4  avg=  18.2  median=  16.0
  detect_ms     min= 180.2  max= 245.0  avg= 210.5  median= 205.0
  encode_ms     min=  45.0  max=  72.1  avg=  55.2  median=  52.0
  base64_ms     min=  18.2  max=  32.1  avg=  24.1  median=  22.0
  total_ms      min= 320.0  max= 420.1  avg= 370.3  median= 358.0
--------------------------------------------------
  Implied FPS (1000 / avg total_ms): 2.7
```

Use this to see which stage dominates (e.g. `detect_ms` or `read_ms`).

---

## 2. Preview Pipeline (what gets measured)

Each `/api/preview` request does:

| Stage | What happens | Typical bottleneck on Pi |
|-------|----------------|---------------------------|
| **read** | `VideoCapture.read()` — pull **3264×2448** frame from camera | USB bandwidth, driver, sensor |
| **resize** | `cv2.resize` down to preview size (e.g. 640×480) | CPU |
| **detect** | ArUco `detectMarkers` + box overlay on preview-sized image | **CPU (often largest)** |
| **encode** | `cv2.imencode` JPEG (software libjpeg) | CPU |
| **base64** | `base64.b64encode` for data URL | CPU, smaller |

Total time ≈ sum of these; FPS ≈ `1000 / total_ms`.

---

## 3. Raspberry Pi 5 – likely bottlenecks

**Pi 5 specs (relevant):** 4× Cortex-A76 @ 2.4 GHz, VideoCore VII GPU, ~17 GB/s memory bandwidth.

The preview path uses **CPU-only** OpenCV (resize, ArUco, imencode). No GPU encode.

### 1. Reading full-resolution every frame

- Camera is set to **3264×2448** for capture.
- Every preview frame reads that full-res image, then we downscale to 640×480 (or smaller).
- That’s ~24 MB raw per frame over USB + CPU work before we ever resize.
- **Impact:** High `read_ms` + unnecessary memory traffic.

### 2. ArUco detection (CPU)

- `detectMarkers` runs on the downsized preview (e.g. 640×480 or 320×240).
- Pure CPU, no GPU acceleration.
- **Impact:** Often the largest share of `total_ms` on Pi (~150–250 ms typical).

### 3. JPEG encoding (CPU)

- `cv2.imencode('.jpg', ...)` uses software libjpeg.
- Pi 5’s VideoCore VII can do hardware encode, but we don’t use it here.
- **Impact:** `encode_ms` grows with resolution and JPEG quality.

### 4. Resize

- `cv2.resize` from 3264×2448 to preview size.
- **Impact:** Usually smaller than detect/encode, but still CPU-bound.

### 5. Base64

- Adds ~33% to payload size and some CPU.
- **Impact:** Generally small compared to detect/encode.

### Summary

- **Most likely main bottleneck:** **ArUco detection** (`detect_ms`), then **read + resize**, then **encode**.
- Benchmark on your Pi to confirm; the script’s per-stage breakdown shows where time goes.

---

## 4. Tuning options (config / env)

All of these are **environment variables** (or `.env`). Restart the app after changing.

### `PREVIEW_WIDTH` (default: 640)

- Preview size (long edge); aspect ratio kept.
- Smaller → less work for resize, detect, and encode.

```bash
# Often the single biggest win on Pi
export PREVIEW_WIDTH=320
```

Try **320** first. If FPS is still low, you can try **240**; ArUco may start to miss markers if the page is small in frame.

### `PREVIEW_JPEG_QUALITY` (default: 85)

- JPEG quality for preview (e.g. 60–85).
- Lower → faster encode, smaller payload.

```bash
export PREVIEW_JPEG_QUALITY=70
# Or more aggressive:
export PREVIEW_JPEG_QUALITY=60
```

### `PREVIEW_RESIZE_INTERPOLATION` (default: linear)

- `linear` (default) vs `nearest`.
- `nearest` is faster, slightly rougher.

```bash
export PREVIEW_RESIZE_INTERPOLATION=nearest
```

### `PREVIEW_DETECT_EVERY_N` (default: 1)

- Run ArUco every **N**-th preview frame; other frames reuse last box.
- Reduces average CPU per frame.

```bash
# Run detection every 2nd frame
export PREVIEW_DETECT_EVERY_N=2
# Every 3rd frame
export PREVIEW_DETECT_EVERY_N=3
```

Preview video still updates every frame; only the overlay updates every N frames. Good trade-off on Pi.

---

## 5. Suggested Pi 5 tuning

Start with:

```bash
export PREVIEW_WIDTH=320
export PREVIEW_JPEG_QUALITY=70
export PREVIEW_RESIZE_INTERPOLATION=nearest
export PREVIEW_DETECT_EVERY_N=2
```

Then run `scripts/benchmark_preview.py` and check:

- `total_ms` and **FPS**
- Which of `read_ms`, `resize_ms`, `detect_ms`, `encode_ms` is largest.

Adjust based on that:

- **`detect_ms`** dominant → try `PREVIEW_DETECT_EVERY_N=3` or `PREVIEW_WIDTH=240`.
- **`encode_ms`** high → try `PREVIEW_JPEG_QUALITY=60` or lower `PREVIEW_WIDTH`.
- **`read_ms`** very high → camera/USB/driver limited; we still need full-res for capture, so we only optimize resize/detect/encode.

---

## 6. Frontend polling

The UI polls `/api/preview` every **100 ms** (`setInterval(..., 100)`). That asks for up to 10 FPS. If the backend is ~2–3 FPS:

- You get 2–3 FPS; the extra polls just wait for the previous response.
- No need to change the interval for benchmarking; improving backend `total_ms` is what matters.

---

## 7. Checklist

1. Run **`scripts/benchmark_preview.py`** and note which stage dominates.
2. Set **`PREVIEW_WIDTH=320`** (and optionally 240 if needed).
3. Set **`PREVIEW_JPEG_QUALITY=70`** (or 60).
4. Set **`PREVIEW_RESIZE_INTERPOLATION=nearest`**.
5. Set **`PREVIEW_DETECT_EVERY_N=2`** (or 3).
6. Restart the app and **benchmark again** to confirm improvement.
7. If FPS is still low, focus on the top 1–2 stages from the benchmark (e.g. ArUco vs encode).

---

## 8. Capture quality unchanged

- **Capture** still uses **3264×2448** for Notion/OCR.
- **Review/process** still uses full-res + `detect_aruco_detailed`.
- Only the **live preview** path is tuned for speed.
