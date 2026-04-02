# Cat Detector (With 100% Artificial Intelligence)

Cat Detection & Beyond: Real-time Telegram alerts for every visitor.

### Video Stream

<img width="2560" height="1600" alt="image" src="https://github.com/user-attachments/assets/491983bc-4af6-42d0-b379-3f883e466fdd" />

### Alerts on Telegram

<img width="1161" height="1422" alt="image" src="https://github.com/user-attachments/assets/a27faee6-d5ea-4194-bc51-1c8b0a15da9c" />

An utility that checks whether a cat exists in:
- a single image
- a video stream (video file, webcam, or RTSP/HTTP stream)
- all images in a folder (batch mode)

## Configuration Files

Copy the provided example files and fill in your own values before first use:

```
secrets.env.EXAMPLE  ->  secrets.env
telegram-send.conf.EXAMPLE  ->  telegram-send.conf
```

`secrets.env` holds private credentials (camera username/password, Telegram bot token) and is never committed to git.
`config.env` holds non-secret runtime defaults such as the default model and snapshot file limit.

## Install

```
pip install -r requirements.txt
```

## Windows Prerequisite

If you are running this project on Windows and `detect_cat.bat` fails during `import torch` with an error mentioning `c10.dll` or DLL initialization, install or update the Microsoft Visual C++ 2015+ Redistributable (x64).

This project was validated on Python 3.14 after upgrading the x64 runtime package to the current release.

Using `winget`:

```powershell
winget install --id Microsoft.VCRedist.2015+.x64 --exact --accept-package-agreements --accept-source-agreements
```

## Windows Quick Start (.bat)

Use the launcher file to run the utility on Windows:

```bat
detect_cat.bat --model yolo26n image --source "Cat Photo Samples\2026-03-22 15.49.09.jpg"
```

It will automatically:
- use `.venv\Scripts\python.exe` when available
- load non-secret defaults from `config.env` if the file exists
- load environment variables from `secrets.env` if the file exists
- pass all arguments through to `cat_detector.py`

Load order is `config.env` first, then `secrets.env` (so secrets can override defaults when needed).

## Supported Options

- `--model` (yolo26n, yolo26s, or path to .pt)
- `--conf` (confidence threshold)
- `--imgsz` (image size)
- `--display` (show annotated video window)
- `--fit-display` (fit preview to screen)
- `--output` (save annotated video)
- `--snapshot-dir` (where to save snapshots)
- `--snapshot-cooldown` (min seconds between snapshots)
- `--snapshot-max-files` (max files in snapshot dir)
- `--telegram-send` (enable Telegram snapshot sending)
- `--telegram-config` (telegram-send.conf path)
- `--alert-person`, `--alert-bird`, `--alert-dog`, `--alert-bear` (enable/disable triggers)
- `--beep-on-cat` (audio alert)
- `--beep-cooldown` (min seconds between beeps)
- `--timing-log` (print timing diagnostics)

### Video Window Controls
- `q` to end
- `h` to show current active options (popup window with dynamically sized font that auto-fits to window)
- `r` to toggle manual recording on/off (saved to `recordings/`)
- `s` to save a manual snapshot (saved to `snapshots_manual/`)

## Changelog
- Added options to disable dog and bear detection
- Video window watermark updated for new controls
- Video window opens maximized by default
- Removed .vbs and extra .bat launcher
- Press `h` in video window to see current options
- Options popup now uses a dynamically sized font that auto-fits the text to the popup window, ensuring all options are visible and readable
- Added interactive recording toggle in the live window (`r`)
- Added blinking `REC` visual cue while recording is active
- Added manual snapshot capture from live window (`s`) with overlay/captions included
- Added short popup confirmation when manual snapshots are saved

Supported built-in aliases:
- `yolo26n` -> `yolo26n.pt`
- `yolo26s` -> `yolo26s.pt`

Model weight files (`*.pt`) are intentionally not committed to git. If a selected model file is missing locally, Ultralytics can download it automatically on first use.

You can choose model in three ways:
- pass alias: `--model yolo26s`
- pass file path: `--model path/to/custom.pt`
- set `CAT_DETECTOR_MODEL` in `config.env` for persistent local defaults
- set `CAT_DETECTOR_MODEL` as a regular environment variable for the current session

Small/distant cat tuning:
- lower `--conf` (for example `0.10`)
- raise `--imgsz` (for example `1280`)
- avoid `--frame-skip` and `--inference-interval` when maximum sensitivity matters

`config.env` example:

```env
CAT_DETECTOR_MODEL=yolo26s
```

PowerShell example:

```powershell
$env:CAT_DETECTOR_MODEL = "yolo26s"
```

## Run on an Image

```bash
python cat_detector.py --model yolo26n image --source path/to/photo.jpg --save out.jpg
```

Output example:

```text
cat_found=True
top_cat_confidence=0.9123
saved_annotated_image=out.jpg
```

## Run on Video / Stream

Video file:

```bash
python cat_detector.py --model yolo26s video --source path/to/video.mp4 --display --output out.mp4
```

Webcam (index 0):

```bash
python cat_detector.py --model yolo26n video --source 0 --display
```

RTSP stream:

```bash
python cat_detector.py --model yolo26s video --source rtsp://user:pass@ip:554/stream --display
```

Tapo C310 by IP (RTSP URL built automatically):

```bash
python cat_detector.py --model yolo26n video --tapo-ip 192.168.1.111 --tapo-username admin --tapo-password YOUR_PASSWORD --tapo-profile main --display
```

For non-interactive testing, limit processing:

```bash
python cat_detector.py --model yolo26s video --tapo-ip 192.168.1.111 --tapo-username admin --tapo-password YOUR_PASSWORD --tapo-profile main --max-frames 100
```

Notes:
- `--tapo-profile main` maps to `stream1`
- `--tapo-profile sub` maps to `stream2`
- In video mode, provide either `--source` or `--tapo-ip`
- Intermittent stream decode/read errors are handled with automatic retry and reconnect attempts instead of immediate crash.
- Snapshot saving and Telegram sending run on a background worker to reduce frame-loop stalls.

When `--display` is enabled, use the bottom-left on-screen controls helper (`q`, `h`, `r`, `s`) for live interaction.
By default, display mode auto-fits the full frame to your screen while preserving aspect ratio (no cropping).
Use `--no-fit-display` if you want raw frame size instead.

Video overlay behavior:
- Status banner is shown on the left side at mid-height.
- Text is red on a pale-yellow background.
- A short two-tone chime (~250 ms) is played when a cat is detected.
- A blinking `REC` cue appears near the bottom-left when manual recording is active.

Alert options:
- `--beep-on-cat` / `--no-beep-on-cat` to enable or disable alert sound
- `--beep-cooldown` to control minimum seconds between alerts (default: 3.0)

Detection tuning:
- `--imgsz` increases inference resolution; this helps small/far cats at the cost of speed
- lower `--conf` if small cats are being missed

Performance options:
- `--frame-skip` skips frames between inference runs in live video mode
- `--inference-interval` enforces a minimum delay between inference runs
- `--capture-buffer-size` sets preferred OpenCV live capture queue depth (default: 1, lower reduces stale-frame delay)
- `--timing-log` prints timing diagnostics for inference, snapshot save, Telegram send, and video write

Live latency tuning:
- If live view is delayed, the most common cause is backlog: inference takes longer than incoming RTSP frame rate, so old frames queue up.
- Keep `--capture-buffer-size 1` to minimize queued stale frames.
- Use light throttling (`--frame-skip 1`) to reduce per-second inference load and help the loop keep up.
- If delay persists, lower model cost first (`--model yolo26n`) and then reduce resolution (`--imgsz 960`) while keeping low confidence.

Snapshot options (video mode):
- A timestamped snapshot is saved whenever a supported trigger class is detected (person, bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe).
- Only trigger classes are passed to the YOLO inference engine (`classes=` filter); unrelated COCO classes such as `train` or `car` are suppressed entirely and will not appear in the overlay.
- `--snapshot-dir` sets output folder (default: `snapshots`)
- `--snapshot-cooldown` sets minimum seconds between snapshots (default: 2.0; `detect_coco.bat` uses 30 s to avoid Telegram flooding)
- `--snapshot-max-files` sets the maximum number of files to keep in the snapshot directory; the oldest files are deleted when the limit is exceeded (default from `SNAPSHOT_MAX_FILES` in `config.env`, or 1000; set to 0 to disable)
- If `--telegram-send` is enabled, snapshots are sent only when a supported trigger detection is present.
- Manual snapshots can be taken any time in display mode by pressing `s`; these are saved to `snapshots_manual/` and include current overlays/captions.

Telegram snapshot delivery:
- Enable with `--telegram-send`
- Bot token can be passed via `--telegram-token` or `TELEGRAM_BOT_TOKEN`
- Chat id can be passed via `--telegram-chat-id` or `TELEGRAM_CHAT_ID`
- Config file path can be set with `--telegram-config` (default: `telegram-send.conf`)

Example:

```bash
python cat_detector.py --model yolo26s video --tapo-ip 192.168.1.111 --tapo-username tapocam --tapo-password YOUR_PASSWORD --display --telegram-send --telegram-chat-id YOUR_CHAT_ID
```

At the end of streaming, the tool prints:

```text
cat_seen_in_stream=True
```

## Run on a Folder (Batch)

```bash
python cat_detector.py --model yolo26n --conf 0.10 batch --source "Cat Photo Samples" --output-dir test_outputs_conf010
```

Example output:

```text
image=photo1.jpg cat_found=True top_cat_confidence=0.2115
image=photo2.jpg cat_found=False top_cat_confidence=0.0000
batch_total_images=2
batch_cat_images=1
batch_no_cat_images=1
saved_annotated_batch_dir=test_outputs_conf010
```

## Recent Validation and Hardening

Latest updates verified in this workspace:
- Model selection is configurable via `--model` aliases (`yolo26n`, `yolo26s`) and optional `CAT_DETECTOR_MODEL` environment variable.
- `yolo26s` was tested on the Tapo stream and completed successfully.
- A matched `yolo26n` vs `yolo26s` comparison run (same frame limit) completed successfully.
- Video mode now handles intermittent decode/read issues with retry and reconnect behavior instead of immediate termination.

Recommended quick validation command:

```bat
detect_cat.bat --model yolo26s video --tapo-ip 192.168.1.111 --tapo-username YOUR_USER --tapo-password YOUR_PASSWORD --tapo-profile main --capture-buffer-size 1 --frame-skip 1 --display --max-frames 300 --beep-cooldown 1.5
```

## Device Selection and Intel GPU Acceleration

The detector now supports an explicit `--device` option for Ultralytics inference routing.

Examples:

```bash
python cat_detector.py --model yolo26s --device auto video --source 0 --display
python cat_detector.py --model yolo26s --device cpu video --source 0 --display
python cat_detector.py --model yolo26s_openvino_model --device GPU video --source 0 --display
```

Notes:
- `--device auto` is the default
- you can also set `CAT_DETECTOR_DEVICE` in your environment or `config.env`
- the program now prints `inference_device_requested=...`
- when available, it also prints `inference_device_effective=...`

For Intel Iris Xe, CUDA and ROCm are not applicable. The practical acceleration path is OpenVINO.

Typical OpenVINO workflow:

```powershell
pip install --upgrade openvino ultralytics
yolo export model=yolo26s.pt format=openvino imgsz=640
python cat_detector.py --model yolo26s_openvino_model --device GPU video --tapo-ip 192.168.1.111 --tapo-username YOUR_USER --tapo-password YOUR_PASSWORD --tapo-profile main --display
```

If Intel GPU execution is unavailable or unstable on your system, retry with the exported OpenVINO model and `--device CPU`.

## M900-CFR OpenVINO Performance Optimization

A comprehensive OpenVINO inference optimization and benchmarking was performed on the M900-CFR machine (Intel Core i3-6100T @ 3.20GHz with 2 cores / 4 threads, Intel HD Graphics 530 GPU).

### Benchmark Results (M900-CFR)

| Scenario | Latency | FPS | Notes |
|----------|---------|-----|-------|
| PyTorch CPU (baseline, current) | 127.82 ms | 7.82 | End-to-end inference on yolo26n.pt |
| OpenVINO CPU (latency mode) | 61.78 ms | 16.16 | OpenVINO IR runtime on CPU |
| OpenVINO GPU (latency mode) | 58.97 ms | 16.92 | OpenVINO IR runtime on Intel HD Graphics 530 |
| OpenVINO CPU (throughput mode) | ~189.67 ms | 20.80 | Multi-stream parallel inference for batch processing |
| OpenVINO GPU (throughput mode) | ~225.75 ms | 17.66 | Multi-stream mode on GPU |

### Key Findings

- **OpenVINO CPU provides 2.07× speedup** over PyTorch CPU baseline for latency-sensitive live monitoring (61.78 ms vs 127.82 ms).
- **OpenVINO GPU provides 2.17× speedup** (58.97 ms vs 127.82 ms) and is optimal for single-inference latency, though GPU model compilation takes ~15.6 seconds one-time overhead.
- **For sustained throughput streaming**, OpenVINO CPU is superior to GPU on this hardware (20.80 FPS vs 17.66 FPS in throughput mode).
- Model export to OpenVINO IR format preserves detection accuracy while enabling hardware-specific optimizations.

## Recording Compatibility Update (Windows)

Recent updates improved manual recording compatibility for stricter MP4 viewers/extensions on Windows.

### What Was Fixed

- Recording writer selection now prefers the Windows Media Foundation backend first on Windows.
- Codec fallback now prioritizes H.264-compatible output (`avc1`) before legacy fallbacks.
- Output writer initialization uses the first processed frame dimensions to avoid size/header mismatches.
- Repeated write failures now disable the writer after the first error to prevent warning spam.
- Interactive recording remembers the last successful codec to reduce repeated probing noise.

### Why This Matters

Some viewers accepted older recordings while others rejected them when the file was written with less compatible stream tagging (for example `FMP4`). The updated backend/codec strategy produces more broadly compatible MP4 files on this machine.

### Runtime Diagnostics

When recording starts, the app now prints selected writer details. Look for:

- `interactive_recording_codec=...`
- `interactive_recording_backend=...`
- `video_writer_codec=...`
- `video_writer_backend=...`

Expected healthy values on this Windows setup are typically H.264-compatible codec output with `CAP_MSMF` backend.

### REC Indicator UX

The `REC` cue animation was changed from hard on/off blinking to a smooth pulse for better visibility and reduced flicker.

### Recommended Configuration for M900-CFR

Use the optimized launcher **`detect_cat_m900_cfr.bat`** which hardcodes the recommended settings:

```bat
--model yolo26n_ov    # OpenVINO-exported nano model (9.7 MB)
--device CPU           # CPU inference (best sustained throughput for continuous streams)
```

Run with:

```powershell
.\detect_cat_m900_cfr.bat
```

This configuration trades ~58 ms per-frame latency (GPU) for reliable sustained throughput monitoring, making it suitable for the M900-CFR's dual-core CPU and integrated GPU architecture.
