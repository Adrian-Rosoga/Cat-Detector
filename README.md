# Cat Detector (With 100% Artificial Intelligence)

Cat Detection & Beyond: Real-time Telegram alerts for every visitor.

<img width="1161" height="1422" alt="image" src="https://github.com/user-attachments/assets/15b930f1-d3ac-4d0b-ac39-efaec4a1123b" />

An utility that checks whether a cat exists in:
- a single image
- a video stream (video file, webcam, or RTSP/HTTP stream)
- all images in a folder (batch mode)

## 0) Configuration Files

Copy the provided example files and fill in your own values before first use:

```
secrets.env.EXAMPLE  ->  secrets.env
telegram-send.conf.EXAMPLE  ->  telegram-send.conf
```

`secrets.env` holds private credentials (camera username/password, Telegram bot token) and is never committed to git.
`config.env` holds non-secret runtime defaults such as the default model and snapshot file limit.

## 1) Install

```
pip install -r requirements.txt
```

## Windows Quick Start (.bat)

Use the launcher file to run the utility on Windows:

```bat
run_cat_detector.bat --model yolo26n image --source "Cat Photo Samples\2026-03-22 15.49.09.jpg"
```

It will automatically:
- use `.venv\Scripts\python.exe` when available
- load non-secret defaults from `config.env` if the file exists
- load environment variables from `secrets.env` if the file exists
- pass all arguments through to `cat_detector.py`

Load order is `config.env` first, then `secrets.env` (so secrets can override defaults when needed).

## 2) Configure YOLO26 Model

By default, the tool loads `yolo26n`.

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

## 3) Run on an Image

```bash
python cat_detector.py --model yolo26n image --source path/to/photo.jpg --save out.jpg
```

Output example:

```text
cat_found=True
top_cat_confidence=0.9123
saved_annotated_image=out.jpg
```

## 4) Run on Video / Stream

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

When `--display` is enabled, press `q` to quit.
By default, display mode auto-fits the full frame to your screen while preserving aspect ratio (no cropping).
Use `--no-fit-display` if you want raw frame size instead.

Video overlay behavior:
- Status banner is shown on the left side at mid-height.
- Text is red on a pale-yellow background.
- A short two-tone chime (~250 ms) is played when a cat is detected.

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

## 5) Run on a Folder (Batch)

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

## 6) Recent Validation and Hardening

Latest updates verified in this workspace:
- Model selection is configurable via `--model` aliases (`yolo26n`, `yolo26s`) and optional `CAT_DETECTOR_MODEL` environment variable.
- `yolo26s` was tested on the Tapo stream and completed successfully.
- A matched `yolo26n` vs `yolo26s` comparison run (same frame limit) completed successfully.
- Video mode now handles intermittent decode/read issues with retry and reconnect behavior instead of immediate termination.

Recommended quick validation command:

```bat
run_cat_detector.bat --model yolo26s video --tapo-ip 192.168.1.111 --tapo-username YOUR_USER --tapo-password YOUR_PASSWORD --tapo-profile main --capture-buffer-size 1 --frame-skip 1 --display --max-frames 300 --beep-cooldown 1.5
```
