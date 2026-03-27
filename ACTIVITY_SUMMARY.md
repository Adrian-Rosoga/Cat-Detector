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
- resilience behavior
- performance options
- small-object tuning guidance
- alert sound behavior
- trigger-class filtering behavior

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