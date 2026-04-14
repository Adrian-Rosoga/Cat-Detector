# Cat Detector Activity Summary

This file summarizes the full activity history for this workspace from the start of the work session until now, including implemented features, issues found, fixes applied, validation performed, and the current state of the project.

## 1. Initial Objective

The project started as a utility to detect whether a cat exists in:
- a single image
- a video stream
- a folder of images

The implementation is based on YOLO26 through Ultralytics and is designed to run on Windows with optional Tapo C310 RTSP stream support.

## 2. Initial Build-Out

The following baseline capabilities were added early in the activity:
- image detection mode
- video detection mode
- batch folder detection mode
- Windows launcher support through batch files
- Python virtual environment setup and dependency installation

Core dependencies:
- ultralytics
- opencv-python
- telegram-send for Telegram delivery

## 3. Camera and Stream Support

Support was added for accessing a Tapo C310 camera by IP address.

Enhancements included:
- automatic RTSP URL construction from camera IP, username, password, and profile
- support for both main and sub RTSP profiles
- live display of the annotated stream

The utility was tested against the camera at 192.168.1.111 during development.

## 4. Display and Alert Improvements

The live detection overlay and alert behavior were refined in multiple steps.

Changes made:
- moved the detection banner to the left side at mid-height
- used red text on a pale-yellow background
- enlarged the font for better visibility
- fixed display truncation so the preview can show the full frame
- added a fit-to-screen option enabled by default
- watermark now reads: Press: q to end; h for active options
- video window opens maximized by default
- press `h` in the video window to see current options

Alert evolution:
- initially added a beep-beep style alert when a cat is detected
- later changed to a 1 kHz tone for 2 seconds
- later replaced that with a much shorter, less intrusive two-tone chime

Current alert behavior:
- a short two-tone chime is played on cat detection
- alert frequency is limited by a configurable cooldown

## 5. Snapshot and Telegram Integration

Snapshot support was added so that timestamped images are saved whenever supported trigger classes are detected.

Telegram support was then added and refined.

Implemented behavior:
- save timestamped snapshots to a configured directory
- optional sending of snapshots with telegram-send
- support for Telegram configuration through telegram-send.conf
- bot token support through environment/config inputs where needed

Configuration cleanup:
- secrets were kept in secrets.env
- telegram-send.conf was used as the runtime telegram-send configuration file

## 6. Model Configuration Improvements

The project originally used a fixed model. This was later generalized.

Enhancements added:
- configurable model selection through --model
- support for model aliases
- initial aliases added: yolo26n and yolo26s
- support for CAT_DETECTOR_MODEL environment variable

Configuration cleanup:
- CAT_DETECTOR_MODEL was identified as non-secret
- it was removed from secrets.env
- a new config.env file was introduced for non-secret defaults
- launchers were updated to load config.env first, then secrets.env

## 7. Detection Trigger Expansion

Snapshot and Telegram triggering originally focused on animal detection. This was expanded.

Supported trigger classes now include:
- person
- bird
- cat
- dog
- horse
- sheep
- cow
- elephant
- bear
- zebra
- giraffe

This ensured that important detections beyond cats also trigger snapshots and Telegram notifications.

## 8. Verification Work

Several validation passes were performed during the activity.

Completed validation included:
- image tests on sample cat photos
- live Tapo stream tests
- yolo26n and yolo26s comparison runs
- four-class validation across cat, dog, bird, and person images
- Telegram continuity tests
- repeated live-stream checks after resilience and performance changes

Observed result:
- both yolo26n and yolo26s completed valid detections for the tested classes
- yolo26s was generally the stronger option

## 9. Stream Resilience Fixes

The stream originally crashed on intermittent decode/read failures, including H.264 decode errors.

This was addressed by adding:
- retry behavior for transient frame read failures
- reconnect attempts after repeated failures
- per-frame exception handling around inference

Result:
- the program became substantially more robust during unstable stream periods
- decode errors no longer immediately terminate the process

## 10. Git and Repository Cleanup

Repository hygiene work was performed during the activity.

Changes included:
- removing generated test output directories from git tracking without deleting local files
- ignoring generated output folders
- ignoring model weight files such as .pt
- ignoring local secrets/config artifacts as appropriate
- untracking MY_README.txt while keeping it locally ignored

This reduced repository noise and kept generated or private files out of version control.

## 11. detect_coco.bat Improvements

The dedicated Tapo launcher was improved several times.

Enhancements included:
- reading camera credentials from secrets.env
- using config.env for the default model
- setting a stronger default model path through CAT_DETECTOR_MODEL
- tuning defaults for small-cat sensitivity
- setting a longer snapshot cooldown to reduce repeated Telegram sends

Current important defaults in the launcher:
- low confidence threshold for small/distant cats
- increased inference image size
- main stream profile
- Telegram enabled
- snapshot cooldown increased to avoid flooding

## 12. Performance Improvements

The user reported that the program was slow, especially when Telegram delivery was involved.

Root cause:
- snapshot writing and Telegram sending were blocking the main frame-processing loop

Fixes applied:
- moved snapshot saving and Telegram sending to a background worker thread using Queue
- added frame throttling controls
- added timing diagnostics

New controls added:
- frame skip
- inference interval
- timing log

Measured timing during testing showed that Telegram sending was much slower than inference and snapshot saving, confirming the value of the background worker design.

## 13. Small-Cat Detection Fix

One major issue during the session was failure to detect a small cat in the live stream.

Initial attempts:
- tested with confidence 0.25
- tested with confidence 0.10
- the cat was still missed

Root cause:
- default inference size of 640 was not sufficient for the small object in the scene

Fix applied:
- added a configurable --imgsz parameter
- passed imgsz to all model.predict call sites
- tuned detect_coco.bat to use a higher inference size

Validation result:
- with lower confidence and higher inference size, the cat was detected successfully in the live stream

## 14. Alert and Filtering Refinements

Two important refinements were made later in the activity.

### 14.1 Alert sound refinement

The previous alert tone was considered too intrusive.

Fix:
- replaced the long 1 kHz alert with a short two-tone chime

### 14.2 False train detection suppression

A false detection of a train appeared in the live overlay.

Root cause:
- the model was still allowed to infer many irrelevant COCO classes for display purposes

Fix:
- restricted video inference to the supported trigger classes only by using the classes filter in YOLO prediction

Result:
- unrelated detections such as train no longer appear in the overlay or processing pipeline

## 15. Misclassification of Upright Small Cat

Another live issue appeared when a small upright cat was misclassified as dog or bird.

Assessment:
- this was judged to be a model-level misclassification rather than a safe software bug fix
- the system still functionally behaved acceptably because dog and bird are also trigger classes
- snapshots, Telegram messages, and alerts still occurred

Decision:
- no unsafe relabeling logic was added
- the code was left unchanged for this case because forced remapping would risk incorrect behavior on real dogs or birds

## 16. Documentation Updates

Documentation was updated throughout the activity.

Files updated during the session included:
- README.md
- MY_README.txt during development, later removed from git tracking
- PROMPTS_USED.md

Documentation additions covered:
- model configuration
- config.env and secrets.env roles

## 17. Recording Playback and UX Stabilization (Windows MP4)

During the latest activity cycle, recording reliability and playback compatibility were improved after reports that some generated MP4 files did not play in the target MPEG4 viewer.

Issues observed:
- MP4 files sometimes opened in OpenCV but were not playable in the target viewer.
- Recording logs showed OpenH264 library/version errors during codec probing.
- Some recordings were produced with FMP4 tagging, which reduced compatibility.
- REC indicator blink looked harsh and visually unstable.

Root causes identified:
- OpenCV FFmpeg path attempted H.264 via OpenH264 on this machine, but local DLL/version mismatch caused repeated initialization errors.
- Codec/backend selection could fall back to less compatible outputs depending on runtime path.
- Writer failures could produce repetitive per-frame warning noise.

Fixes applied:
- Added robust video-writer creation helper with codec fallback support.
- Added lazy writer initialization for output recording using actual processed frame dimensions.
- Added fail-fast behavior: disable writer after first write failure to prevent repeated warning spam.
- Added interactive codec reuse to reduce repeated probe noise across start/stop cycles.
- Updated backend selection to prefer Windows Media Foundation on Windows, which produced H.264-playable MP4 on this system.
- Added runtime logging of selected codec and backend for both output and interactive recording.
- Updated REC indicator from hard on/off blink to a smooth pulse animation for better UX.

Validation performed:
- Local recording files were inspected using OpenCV metadata reads.
- Backend/codec matrix checks confirmed CAP_MSMF + avc1/h264 path is viable.
- Post-fix test recording confirmed writer opened with H.264 decode signature and valid first-frame read.

Current state:
- Recording is stable.
- REC cue animation is smooth.
- Recent recordings are generated through a viewer-compatible path on this Windows setup.

## 17. Prompt History Maintenance

PROMPTS_USED.md was originally updated incrementally and became incomplete.

Issue:
- later prompts were missed because the file was updated in batches instead of after every user request

Fix:
- the prompt history was reviewed and expanded to include the missing prompts from the later stages of the activity

## 18. Commit History During This Activity

Important commits created during this work included:
- de17581: stop tracking model weights and ignore .pt files
- 3004d24: add imgsz tuning for small-cat detection, async snapshot worker, throttling, and timing diagnostics
- b2608ad: tune alerts and filtering for live detection

## 19. Current Project State

The project now includes:
- configurable YOLO model aliases and defaults
- image, video, and batch detection modes
- Tapo C310 RTSP support
- robust stream retry and reconnect handling
- live display with full-frame fit behavior
- short non-intrusive cat alert chime
- timestamped snapshots
- optional Telegram delivery through telegram-send
- background worker for snapshot saving and Telegram sending
- configurable sensitivity via confidence and inference size
- class filtering to suppress irrelevant detections such as train

## 20. Known Limitations

Remaining limitations that were identified but not force-fixed:
- small or unusually posed cats can still be misclassified by the underlying model
- this is a model-quality issue rather than a safe rule-based code fix
- a stronger or fine-tuned model would be the safest long-term solution

## 21. Operational Guidance

For best small-cat sensitivity in live detection:
- use yolo26s
- use a low confidence threshold such as 0.10
- use a larger inference size such as 1280
- avoid frame skipping and artificial inference delays when sensitivity matters most
- use the main Tapo stream profile instead of the sub-stream

## 22. Summary

From the beginning of the activity to now, the Cat Detector evolved from a simple cat detection utility into a more complete live-monitoring tool with:
- better configurability
- stronger resilience
- improved live usability
- asynchronous notification delivery
- better small-object sensitivity
- cleaner repository/config management
- more accurate on-screen behavior through class filtering

The project is currently in a substantially stronger state than at the start of the activity and is usable for live cat monitoring on the Tapo camera with Telegram notifications.

Additional improvements since the sections above:
- stable status banner (no flicker during frame-skip/latency mode)
- automatic snapshot directory pruning to prevent unbounded disk growth
- example configuration files for new users
- snapshots directory fully removed from git tracking

## 23. Live Latency Investigation and Mitigation

After the previous improvements, a new runtime issue was reported: live display lag of roughly 20 seconds.

Explanation:
- when inference throughput is slower than incoming RTSP frame rate, frames accumulate in capture buffers
- OpenCV then serves older queued frames, causing the preview to show delayed history rather than near-real-time output
- high-cost settings (for example higher inference size with heavier model) increase this risk

Safe mitigations implemented:
- added a configurable `--capture-buffer-size` video argument (default: 1)
- applied capture buffer size on initial stream open and on reconnect open
- tuned `detect_coco.bat` defaults to include `--capture-buffer-size 1`
- tuned `detect_coco.bat` defaults to include light load shedding via `--frame-skip 1`

Operational recommendation after this change:
- prefer `capture-buffer-size=1` for live monitoring freshness
- if lag still appears, reduce model cost first (`yolo26n`) and then reduce `imgsz` while keeping low confidence for small-cat sensitivity

## 24. NO CAT Banner Flicker Fix

After adding frame-skip and inference-interval latency controls, the NO CAT banner began flickering during non-inference display frames.

Root cause:
- skipped and throttled frames were shown raw without the status banner
- this caused the banner to appear only on inference frames and disappear on all others

Fix applied:
- added a `last_status_text` variable to hold the most recently computed banner label
- on every non-inference display frame the last known banner is redrawn onto a copy of the raw frame
- the latency improvement was fully preserved; only overlay rendering was changed

Result:
- banner is stable and no longer flickers during live viewing

## 25. Snapshot Directory Pruning

No upper bound existed on the number of files in the snapshot directory, which could eventually exhaust disk space.

Fix applied:
- added a `prune_snapshots()` helper that sorts files by modification time and deletes the oldest when the file count exceeds the configured limit
- pruning runs inside the existing background snapshot worker thread after each save, so it does not affect the main frame loop
- added `--snapshot-max-files` CLI argument (default from `SNAPSHOT_MAX_FILES` env var, fallback 1000; set to 0 to disable)
- added `SNAPSHOT_MAX_FILES=1000` to `config.env`

## 26. Example Configuration Files for New Users

New users had no reference for the format of `secrets.env` and `telegram-send.conf`.

Fix:
- created `secrets.env.EXAMPLE` with all real values replaced by obvious placeholders
- created `telegram-send.conf.EXAMPLE` with the same treatment
- both files are committed to the repository so new users can copy and fill them in

## 27. Snapshots Directory Removed from GitHub

Despite `snapshots/` being listed in `.gitignore`, the snapshot JPEG files were previously committed and remained tracked, so they continued to appear on GitHub.

Fix:
- ran `git rm -r --cached snapshots/` to remove all tracked snapshots from the git index
- the files remain locally; future snapshots will be properly ignored

## 28. Usability and Directory Improvements

- Removed detect.cat.vbs and detect_cat_launcher.bat (no longer needed; video window now opens maximized and watermark shows all controls)
- Renamed "Snapshots - Hits and some misses" to "Some hits, some misses" for clarity.
- Fixed video overlay watermark so "Press: q to end; h for active options" is always visible and never flickers, regardless of frame skipping or latency settings.

## 29. Popup Font Auto-Fit Enhancement

The options popup window (shown by pressing 'h' in the video window) now automatically adjusts the font size so that all current options fit within the popup window. This ensures the text is always readable and avoids overflow, regardless of the number of options or window size. The font size is dynamically calculated based on the window and text content.

## 30. Device Selection and Intel OpenVINO Support

To support Intel hardware more explicitly, inference device selection was added to the CLI.

Changes made:
- added global `--device` option with `auto` default
- added `CAT_DETECTOR_DEVICE` environment/config support
- passed the selected device through all YOLO predict paths in image, video, and batch modes
- added runtime diagnostics to print requested and effective inference device values when available

Practical outcome:
- the project can now be run more explicitly on CPU or on backends that Ultralytics/OpenVINO can use
- this is especially relevant for Intel Iris Xe systems, where CUDA and ROCm are not available and OpenVINO is the realistic acceleration path

Documentation was also updated to describe:
- how to use `--device`
- how to export a model to OpenVINO format
- how to run the detector with an OpenVINO-exported model targeting Intel GPU or CPU
- resilience behavior
- performance options
- small-object tuning guidance
- alert sound behavior
- trigger-class filtering behavior

## 31. Intel PyTorch Wheel Investigation

An attempt was made to install Intel-optimized PyTorch builds from the official Intel wheel index:

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/intel
```

Findings:
- `torch` and `torchvision` were already present but as the plain CPU build (`2.11.0+cpu`)
- `torchaudio` is not published on the Intel index at all
- A force-reinstall of `torch` from the Intel index also failed with no matching distribution
- Root cause: the Intel XPU wheel index only publishes wheels for Python 3.8–3.11; the project virtual environment uses Python 3.13.2

`torch.xpu.is_available()` returned `False` confirming no Intel XPU support is active.

Options available:
1. Wait for Intel to publish Python 3.13 wheels (no public timeline)
2. Downgrade the project venv to Python 3.11 and reinstall from the Intel index
3. Use the OpenVINO path instead: export the model with `yolo export format=openvino` and run with `--device CPU` or `--device GPU`

Option 3 (OpenVINO) is the most practical with the current Python 3.13 setup and does not require Intel PyTorch wheels.

## 32. OpenVINO Export and Benchmarking

Option 3 (OpenVINO) was pursued. OpenVINO 2026.0.0 was installed and both YOLO models were exported to OpenVINO IR format.

Steps performed:
- installed `openvino` and `openvino-telemetry` via pip (Python 3.13 compatible)
- confirmed OpenVINO devices: `['CPU', 'GPU']` — Intel Iris Xe is visible as `GPU`
- exported `yolo26s.pt` → `yolo26s_openvino_model/` (36.7 MB)
- exported `yolo26n.pt` → `yolo26n_openvino_model/` (9.7 MB)

Benchmark results (640×640 dummy frame, 5 runs average):
- OpenVINO CPU: 315 ms/frame
- PyTorch CPU:  238 ms/frame
- Speedup: 0.75× (OpenVINO CPU was slower on this hardware)

Notes on GPU routing:
- OpenVINO's `Core().available_devices` does include `GPU` (Intel Iris Xe)
- Ultralytics' `select_device()` is PyTorch-focused and rejects `device='GPU'` — it only accepts CUDA device references
- True GPU routing via OpenVINO would require deeper integration beyond what the `--device` argument currently supports through Ultralytics

Conclusion:
- PyTorch CPU inference is already well-optimised on the Intel i7-1360P for this model size
- OpenVINO CPU does not provide a speedup on this machine via the Ultralytics wrapper
- The exported OpenVINO models are retained and usable via the new `--model yolo26s_ov` and `--model yolo26n_ov` aliases added to the code

## 33. M900-CFR OpenVINO Optimization and Benchmarking

### Objective
Optimize inference performance for the M900-CFR deployment machine (Intel Core i3-6100T @ 3.20 GHz, 2 cores / 4 threads, Intel HD Graphics 530 GPU).

### Hardware Profile

**M900-CFR Machine Specifications:**
- **CPU:** Intel Core i3-6100T @ 3.20 GHz (2 cores / 4 logical threads)
- **GPU:** Intel HD Graphics 530 (integrated)
- **Comparison Note:** Much more modest hardware than the i7-1360P tested in section 32; this is a 6th-generation Skylake system with limited compute resources.

### OpenVINO Installation and Export

OpenVINO 2026.0.0 was installed and the YOLO26 models were exported to OpenVINO IR format:
- `yolo26n_openvino_model/` exported and saved (9.7 MB, ~48% of .pt size)
- `yolo26s_openvino_model/` exported and saved (36.7 MB, ~56% of .pt size)
- Both models confirmed compatible with available device list: `['CPU', 'GPU']`

### Comprehensive Benchmark Results (M900-CFR)

Three separate benchmarking approaches were performed to ensure confidence in the results:

#### 1. PyTorch CPU Baseline (End-to-End)
- Model: `yolo26n.pt`
- Method: Repeated `model.predict()` calls on one snapshot image
- Runs: 30 iterations with warmup
- **Average Latency:** 127.82 ms
- **Estimated FPS:** 7.82 FPS
- **Inference Range:** 118.39 ms (min) to 143.76 ms (max)

#### 2. OpenVINO Throughput Mode Benchmarks
Using `benchmark_app -hint throughput` with 4 parallel inference requests over 30+ seconds:

**OpenVINO CPU (Throughput Mode):**
- Iterations: 628
- Duration: 30189.62 ms
- **Average Latency:** 191.92 ms
- **Throughput:** 20.80 FPS
- Range: 114.04–454.56 ms

**OpenVINO GPU (Throughput Mode, Intel HD Graphics 530):**
- Iterations: 536
- Duration: 30353.89 ms
- **Average Latency:** 225.75 ms
- **Throughput:** 17.66 FPS
- Range: 86.72–259.00 ms

#### 3. OpenVINO Latency Mode Benchmarks
Using `benchmark_app -hint latency` with synchronous single-request inference:

**OpenVINO CPU (Latency Mode):**
- Iterations: 243
- Duration: 15037.86 ms
- **Average Latency:** 61.78 ms
- **Throughput:** 16.16 FPS
- Median: 58.37 ms
- Range: 53.59–259.31 ms

**OpenVINO GPU (Latency Mode, Intel HD Graphics 530):**
- Iterations: 254
- Duration: 15008.22 ms
- **Average Latency:** 58.97 ms
- **Throughput:** 16.92 FPS
- Median: 58.81 ms
- Range: 56.94–68.28 ms

### Analysis and Conclusions

#### PyTorch CPU Performance
The current baseline (PyTorch CPU yolo26n) achieves 7.82 FPS (127.82 ms per frame), which is significantly slower than the OpenVINO-exported alternatives.

#### OpenVINO CPU vs OpenVINO GPU
- **GPU Latency:** Slightly better (58.97 ms vs 61.78 ms), ~1.05× faster
- **GPU Throughput Mode:** Worse (17.66 FPS vs 20.80 FPS), -15% performance
- **GPU Compile Time:** Much slower (~15.6 seconds one-time overhead vs CPU ~0.67 seconds)
- **Verdict:** For continuous stream workloads, CPU is more practical; GPU marginally faster for single-frame requests with acceptable warmup cost

#### Relative Speedups

| Comparison | Speedup Factor |
|------------|----------------|
| OpenVINO CPU vs PyTorch CPU baseline | 2.07× |
| OpenVINO GPU vs PyTorch CPU baseline | 2.17× |
| OpenVINO GPU vs OpenVINO CPU | 1.05× (latency mode only) |

### Recommendation for M900-CFR

For the M900-CFR system (continuous stream monitoring), the optimized configuration is:

```bat
--model yolo26n_ov     # OpenVINO-exported nano model
--device CPU            # CPU inference (better sustained throughput)
```

**Rationale:**
1. OpenVINO CPU delivers 2.07× speedup over the current PyTorch baseline
2. CPU provides consistent 20.80 FPS in throughput mode best suited for continuous video streams
3. No GPU warmup overhead eliminates initial ~15-second startup delay
4. Dual-core CPU system benefits from predictable CPU-targeted optimizations

**Deployment Artifact:**
- Created `detect_cat_m900_cfr.bat` with the recommended settings hardcoded for easy adoption

### Notes on GPU Routing

Intel HD Graphics 530 is correctly detected by OpenVINO as `GPU` device and can be used, but:
- GPU routing requires direct OpenVINO Core API usage, not via Ultralytics' device wrapper
- The current `--device GPU` in the Ultralytics path expects CUDA devices and rejects generic Intel GPU identifiers
- Full GPU acceleration would require deeper integration beyond the current `--device` argument scope
- For this reason, CPU inference is the practical recommendation despite slightly higher per-frame latency

## 34. Interactive Recording and Manual Snapshot Controls

Live window keyboard controls were expanded for manual capture workflows.

Enhancements added:
- press `r` to toggle recording on/off in the live video window
- recording files are saved to a dedicated `recordings/` directory
- press `s` to save a manual snapshot with current overlays/captions
- manual snapshots are saved to `snapshots_manual/`

Implementation details:
- added an independent interactive `cv2.VideoWriter` separate from `--output`
- recording output uses timestamped filenames
- manual snapshots are timestamped to the millisecond
- key handling was updated consistently across all display branches

## 35. Visual Recording State and Helper Overlay Refinements

The live display now provides clearer in-window feedback and cleaner overlay layout.

Changes made:
- added a bottom-left `REC` visual cue while interactive recording is active
- made the `REC` cue blink to indicate active recording
- moved helper banner and `REC` cue upward to avoid overlap
- updated helper banner text to show current window controls

Current helper controls shown on-screen:
- q = quit
- h = options popup
- r = recording toggle
- s = manual snapshot

## 36. Manual Snapshot Popup Notification

After taking a manual snapshot, the app now shows a short confirmation popup.

Behavior:
- displays "Snapshot saved!" in a small topmost popup window
- popup closes automatically after a short interval
- popup runs in a daemon thread to avoid blocking frame processing

## 37. Banner Font, Recording Audio, and Live Audio Playback

This activity cycle focused on three related areas:
- making the status banner typography consistent
- adding audio to interactive MP4 recordings
- adding live source-audio playback on the PC with runtime control

### 37.1 Status Banner Typography

Issue:
- `CAT DETECTED` and `NO CAT YET` were rendered with different font faces/thickness values, so the detected-state banner looked noticeably weaker.

Fix applied:
- unified the banner renderer so both statuses use the same bold `FONT_HERSHEY_DUPLEX` styling and thickness.

Result:
- `CAT DETECTED` now matches the stronger visual weight previously used by `NO CAT YET`.

### 37.2 Interactive Recording Audio: Attempts That Did Not Work

Several recording-audio approaches were tried before converging on the working implementation.

#### Attempt 1: Microphone capture

What was tried:
- added optional microphone capture using Python audio libraries and planned to mux mic audio into the recorded MP4.

Why it was rejected:
- the actual requirement was to capture the audio already present in the RTSP/video source stream, not a local microphone.

Outcome:
- removed as the wrong design for this camera setup.

#### Attempt 2: Source-stream audio via ffmpeg, but relying on PATH

What was tried:
- started a sidecar ffmpeg process to capture source audio while OpenCV wrote the MP4 video.

Problem observed:
- audio capture failed immediately because `ffmpeg` was not in `PATH`.

Fix applied:
- added ffmpeg auto-discovery using:
	- `FFMPEG_PATH`
	- system `PATH`
	- local `ffmpeg.exe`
	- bundled `imageio-ffmpeg`

Outcome:
- ffmpeg became available reliably from the virtual environment.

#### Attempt 3: RTSP native audio-copy path

What was tried:
- captured the RTSP audio stream directly using ffmpeg stream-copy into a Matroska sidecar, intending to preserve the original G.711 path more directly.

Why it did not work well:
- this path introduced a regression where the audio capture process exited immediately on the tested setup and was less reliable than the decoded PCM path.

Outcome:
- reverted.

#### Attempt 4: Source audio capture with unsupported ffmpeg option

What was tried:
- added `-rw_timeout` for RTSP input handling.

Problem observed:
- the bundled ffmpeg binary did not support that option, causing the capture process to fail immediately.

Validation finding:
- direct probing showed the exact failure was `Option rw_timeout not found.`

Fix applied:
- removed `-rw_timeout` from the ffmpeg command.

Outcome:
- source-audio capture started working again.

#### Attempt 5: Ungraceful audio-process shutdown

What was tried:
- recording audio capture was stopped with process termination.

Problem observed:
- the WAV sidecar was sometimes not finalized correctly, so no usable audio file existed at stop time.

Fix applied:
- changed shutdown to send `q` to ffmpeg via stdin first, then fall back to terminate/kill only if needed.

Outcome:
- sidecar WAV files finalized correctly and could be muxed.

### 37.3 Interactive Recording Audio: What Worked

Final working design:
- while interactive recording is active, OpenCV writes the annotated MP4 video frames
- a separate ffmpeg process captures source audio from the RTSP stream into a temporary WAV sidecar
- on stop, the sidecar WAV is muxed back into the MP4 as AAC audio
- the temporary WAV is deleted after a successful mux

Enhancements added:
- audio gain during mux so very quiet source audio becomes audible in the final MP4
- configurable recording-audio gain via `--record-audio-gain-db`
- clear log lines for recording start, audio start, mux success, stop, and warnings

Validation performed:
- ffmpeg metadata inspection confirmed generated MP4 files contain both:
	- H.264 video
	- AAC audio
- volume analysis showed earlier captures were extremely quiet, which justified the mux gain stage
- later recordings produced audible audio successfully in the final MP4

Result:
- interactive MP4 recordings now include working audio from the source stream.

### 37.4 Live Source Audio on the PC: Attempts That Did Not Work

#### Attempt 1: ffplay-only live playback

What was tried:
- use ffplay to play the source audio live on the PC while video continued to display in OpenCV.

Problem observed:
- the environment had ffmpeg but not ffplay.

Outcome:
- live audio could not work with an ffplay-only implementation.

#### Attempt 2: First fallback object missing process interface

What was tried:
- introduced a Python fallback backend that pipes ffmpeg-decoded PCM into `sounddevice` for speaker playback.

Problem observed:
- the supervisor logic expected a subprocess-like object and called `.poll()`, but the fallback player object did not implement it.

Fix applied:
- added a subprocess-compatible `poll()` method.

Outcome:
- crash removed and the fallback backend could stay under the existing supervision logic.

### 37.5 Live Source Audio on the PC: What Worked

Final working design:
- live source audio is enabled by default
- pressing `a` toggles live audio on/off at runtime
- `--play-audio` and `--no-play-audio` control startup behavior
- if ffplay is unavailable, a fallback backend uses:
	- ffmpeg to decode RTSP/source audio to PCM
	- `sounddevice` to play that PCM on local speakers

UI changes:
- helper watermark now shows the audio toggle and current on/off state
- startup controls text includes the `a` toggle

Result:
- live source audio on the PC works well on the current setup.

### 37.6 Interaction Between Live Audio and Recording Audio

New issue introduced:
- once live audio worked, MP4 recording audio regressed because the live playback backend was already consuming the source audio stream.
- a second separate recording-audio capture process then failed on this setup.

Fix applied:
- the live ffmpeg-pipe audio backend was extended to tee its already-decoded PCM stream into a WAV sidecar whenever interactive recording is active.
- recording now reuses the live audio pipeline rather than competing with it.

Result:
- both features work at the same time:
	- live source audio playback on the PC
	- MP4 recordings with embedded audio

### 37.7 Live Audio Volume Control

Final enhancement in this cycle:
- live audio was made louder by default and configurable.

What was added:
- live playback gain in dB is now applied to both live-audio backends
- new CLI option: `--play-audio-gain-db`
- new config/env-backed default: `CAT_DETECTOR_PLAY_AUDIO_GAIN_DB`
- `config.env` now includes:
	- `CAT_DETECTOR_PLAY_AUDIO_GAIN_DB=12.0`

Result:
- live audio volume can now be increased or decreased without code changes.

### 37.8 Final State After This Activity Cycle

Working now:
- consistent bold status banner for both detection states
- interactive MP4 recording with working embedded source audio
- live source-audio playback on the PC
- runtime live-audio toggle with `a`
- configurable live-audio gain through CLI and `config.env`
- configurable recording-audio gain during mux

What did not survive to the final design:
- microphone-based recording audio
- ffplay-only live playback dependency
- RTSP native audio-copy sidecar path
- `-rw_timeout` ffmpeg option on this bundled ffmpeg build
- separate competing audio-capture process when live playback is already active

## 38. Image Mode: Cats-Only Detection Filter

### Issue
When running image detection mode, the annotated output included all 80 COCO classes (persons, motorcycles, birds, etc.), not just cats. This was inconsistent with the video mode, which already filtered inference to trigger classes only.

### Root Cause
The `detect_image()` function's `model.predict()` call did not pass a `classes=` filter, so all COCO classes were returned and drawn on the annotated image.

### Fix Applied
- Added `classes=sorted(cat_ids)` to the `model.predict()` call in `detect_image()`, matching the filtering approach already used in video mode.

### Result
- Image mode now only detects and annotates cats, consistent with the tool's purpose.

## 39. Large Image Detection Failure (Istanbul Cats Test Case)

### Issue
An image with 10 visible cats (`Istanbul Cats - 2026-04-05 15.10.41.jpg`, 4000×2252 resolution) returned `cat_found=False` with `top_cat_confidence=0.0000` when using the default settings (`yolo26n`, `imgsz=640`).

### Root Cause
The default `imgsz=640` downscales a 4000×2252 image by ~6×, reducing cats to ~30–60 pixels in the inference frame — too small for reliable detection, especially with the nano model.

### Diagnostic Results
At `imgsz=640` with `conf=0.01`, the highest cat confidence was only 0.0326 (3.3%), far below the 0.25 threshold.

At `imgsz=1280`:
- `yolo26n` (nano): detected 3 cats above 0.25 threshold
- `yolo26s` (small): detected **10 cats** above 0.25 threshold with high confidence (0.70–0.92)

### Recommendation
For high-resolution images with many small/medium subjects, use `--model yolo26s --imgsz 1280` or higher.

## 40. Datetime Timestamps in Log Messages

### Change
All log messages now include a `[YYYY-MM-DD HH:MM:SS]` datetime timestamp prefix.

### Implementation
- Added `from datetime import datetime` import.
- Modified the custom `print()` function to prepend a formatted timestamp to every log line.

### Example Output
```
[2026-04-14 05:01:34] INFO: test_message=hello
[2026-04-14 05:01:55] WARN: stream_reconnect_warning=...
```

## 41. RTSP Stream Connection Resilience Overhaul

### Issue
When WiFi was disabled to simulate a stream failure, the program silently hung and eventually stopped with only an h264 decode error — no reconnection was attempted.

### Root Causes Identified

**1. No RTSP-over-TCP transport:**
OpenCV's `cv2.VideoCapture` defaults to UDP for RTSP, which is unreliable (packet loss, firewall/NAT issues). The ffmpeg audio components of the code already used `-rtsp_transport tcp`, but the main video capture did not.

**2. Reconnection counter bug:**
After a failed reconnect where `cap.isOpened()` returned `False`, the `consecutive_read_failures` counter was never reset. This meant the next single `cap.read()` failure immediately triggered another reconnect attempt (instead of getting a fresh 15-frame retry window). All 20 reconnect attempts burned through in ~20 seconds with no real recovery.

**3. No backoff between reconnects:**
The original code waited a flat 1 second between reconnect attempts. For network outages, this was too aggressive — the camera/network had no time to recover.

**4. `cap.read()` hangs indefinitely on stream death:**
When the RTSP stream dies mid-transfer, `cap.read()` calls into FFmpeg which blocks waiting for the next TCP packet — with no timeout. The h264 decode error was the last frame FFmpeg partially decoded before it stalled forever. The program never reached the reconnection logic because it was stuck inside `cap.read()`.

### Fixes Applied

**RTSP-over-TCP transport:**
- Added `OPENCV_FFMPEG_CAPTURE_OPTIONS=rtsp_transport;tcp|stimeout;10000000|timeout;10000000` for RTSP sources.
- Video capture now uses `cv2.CAP_FFMPEG` backend explicitly for RTSP URLs.
- The `stimeout` (10s socket timeout) and `timeout` (10s I/O timeout) tell FFmpeg to abort if no data arrives within 10 seconds.

**Reconnection counter fix:**
- `consecutive_read_failures` is now always reset after each reconnect attempt, giving each attempt a fair 15-frame retry window.
- The max-attempts check is performed before releasing/reopening the capture, avoiding wasted reconnect work.

**Exponential backoff:**
- Replaced the flat 1-second delay with exponential backoff: 2s → 3s → 4.5s → ... up to 15s max.
- This gives the camera and network more time to recover between attempts.

**Threaded read with timeout:**
- `cap.read()` now runs in a daemon thread with a 15-second join timeout.
- If FFmpeg's own timeout doesn't trigger, the main loop detects the hang, logs `stream_read_warning=cap.read() timed out after 15s`, and proceeds to reconnection.

**Broader exception handling:**
- Changed `except cv2.error` to `except Exception` around the read operation, catching any unexpected error type from the FFmpeg backend.

**Reconnection info message:**
- Added `stream_reconnected=True` log message when a reconnect succeeds, providing clear visibility into recovery events.

**Centralized capture creation:**
- Extracted `_open_capture()` helper function used by both initial connection and reconnection, ensuring consistent RTSP options and buffer size configuration.

### Result
- The program no longer hangs silently when the stream drops.
- Reconnection attempts are properly spaced and logged with timestamps.
- Successful reconnections are confirmed with an info message.
- The stream recovers automatically when the network is restored.
