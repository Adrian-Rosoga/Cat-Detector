import argparse
import ctypes
import os
from queue import Queue
import subprocess
import threading
import time
from urllib.parse import quote
from typing import Iterable, Set, Union

import cv2
from ultralytics import YOLO

try:
    import winsound
except ImportError:
    winsound = None


MODEL_ALIASES = {
    "yolo26n": "yolo26n.pt",
    "yolo26s": "yolo26s.pt",
}


def resolve_model_path(model_value: str) -> str:
    """Resolve a configured model alias to a weights file path."""
    normalized = model_value.strip()
    if not normalized:
        raise RuntimeError("Model value cannot be empty.")

    lowered = normalized.lower()
    if lowered in MODEL_ALIASES:
        return MODEL_ALIASES[lowered]

    if lowered.endswith(".pt"):
        stem = lowered[:-3]
        if stem in MODEL_ALIASES:
            return MODEL_ALIASES[stem]

    return normalized


def parse_source(source: str) -> Union[int, str]:
    """Convert numeric camera index strings to int, leave other sources unchanged."""
    if source.isdigit():
        return int(source)
    return source


def build_tapo_rtsp_url(ip: str, username: str, password: str, profile: str) -> str:
    """Build an RTSP URL for a Tapo C310 camera profile."""
    stream_path = "stream1" if profile == "main" else "stream2"
    safe_user = quote(username, safe="")
    safe_password = quote(password, safe="")
    return f"rtsp://{safe_user}:{safe_password}@{ip}:554/{stream_path}"


def resolve_video_source(args: argparse.Namespace) -> tuple[Union[int, str], str]:
    """Resolve either a generic source or a Tapo-derived RTSP source."""
    if args.tapo_ip:
        if not args.tapo_username or not args.tapo_password:
            raise RuntimeError(
                "When using --tapo-ip, provide both --tapo-username and --tapo-password."
            )

        source = build_tapo_rtsp_url(
            args.tapo_ip,
            args.tapo_username,
            args.tapo_password,
            args.tapo_profile,
        )
        display_source = f"rtsp://<user>:<password>@{args.tapo_ip}:554/{'stream1' if args.tapo_profile == 'main' else 'stream2'}"
        return source, display_source

    if not args.source:
        raise RuntimeError("Provide either --source or --tapo-ip for video mode.")

    source = parse_source(args.source)
    return source, str(args.source)


def draw_status_banner(frame, text: str) -> None:
    """Draw status text in the left-middle with red text on pale-yellow background."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 2.7
    thickness = 2
    margin_x = 12
    margin_y = 14
    text_size, baseline = cv2.getTextSize(text, font, scale, thickness)
    text_width, text_height = text_size

    x1 = margin_x
    banner_height = text_height + baseline + 10
    center_y = frame.shape[0] // 2
    y1 = max(margin_y, center_y - banner_height // 2)
    y2 = y1 + banner_height
    x2 = x1 + text_width + 16

    cv2.rectangle(frame, (x1, y1), (x2, y2), (200, 240, 255), thickness=-1)
    cv2.putText(
        frame,
        text,
        (x1 + 8, y2 - 8),
        font,
        scale,
        (0, 0, 255),
        thickness,
        cv2.LINE_AA,
    )


def play_beep_beep_alert() -> None:
    """Play a short, non-intrusive two-tone chime."""
    if winsound is not None:
        winsound.Beep(880, 90)
        time.sleep(0.04)
        winsound.Beep(1175, 120)
    else:
        print("\a", end="", flush=True)


def get_screen_size() -> tuple[int, int]:
    """Return current screen size for display fitting."""
    try:
        user32 = ctypes.windll.user32
        return int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1))
    except Exception:
        return 1920, 1080


def fit_frame_to_screen(frame, max_width: int, max_height: int):
    """Scale frame down to fit screen bounds while preserving aspect ratio."""
    height, width = frame.shape[:2]
    if width <= 0 or height <= 0:
        return frame

    scale = min(max_width / width, max_height / height, 1.0)
    if scale >= 1.0:
        return frame

    new_width = max(1, int(width * scale))
    new_height = max(1, int(height * scale))
    return cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)


def get_snapshot_trigger_class_ids(names: Union[dict, list]) -> Set[int]:
    """Resolve class ids that should trigger snapshots and Telegram sends."""
    trigger_names = {
        "person",
        "bird",
        "cat",
        "dog",
        "horse",
        "sheep",
        "cow",
        "elephant",
        "bear",
        "zebra",
        "giraffe",
    }
    trigger_ids: Set[int] = set()

    if isinstance(names, dict):
        for class_id, class_name in names.items():
            if str(class_name).strip().lower() in trigger_names:
                trigger_ids.add(int(class_id))
    elif isinstance(names, Iterable):
        for class_id, class_name in enumerate(names):
            if str(class_name).strip().lower() in trigger_names:
                trigger_ids.add(class_id)

    return trigger_ids


def frame_has_any_class(result, class_ids: Set[int]) -> bool:
    """Return True when at least one detection belongs to provided class ids."""
    if result.boxes is None or len(result.boxes) == 0:
        return False

    for cls_id in result.boxes.cls.tolist():
        if int(cls_id) in class_ids:
            return True
    return False


def write_telegram_config(config_path: str, token: str, chat_id: str) -> None:
    """Write a telegram-send config file with token and chat id."""
    config_text = "\n".join(
        [
            "[telegram]",
            f"token = {token}",
            f"chat_id = {chat_id}",
            "",
        ]
    )
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_text)


def send_snapshot_via_telegram(
    args: argparse.Namespace, snapshot_path: str, trigger_detected: bool
) -> None:
    """Send a snapshot image with telegram-send when enabled."""
    if not args.telegram_send:
        return

    command = ["telegram-send"]
    if args.telegram_config:
        command.extend(["--config", args.telegram_config])

    if trigger_detected:
        caption = f"Person/animal/bird detected at {time.strftime('%Y-%m-%d %H:%M:%S')}"
    else:
        caption = f"Stream snapshot at {time.strftime('%Y-%m-%d %H:%M:%S')}"
    command.extend(["-i", snapshot_path, "--caption", caption])

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        print("telegram_send_error=telegram-send command not found")
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        if stderr:
            print(f"telegram_send_error={stderr}")
        else:
            print("telegram_send_error=telegram-send failed")


def get_cat_class_ids(names: Union[dict, list]) -> Set[int]:
    """Resolve all class ids named exactly 'cat' in the loaded model."""
    cat_ids: Set[int] = set()

    if isinstance(names, dict):
        for class_id, class_name in names.items():
            if str(class_name).strip().lower() == "cat":
                cat_ids.add(int(class_id))
    elif isinstance(names, Iterable):
        for class_id, class_name in enumerate(names):
            if str(class_name).strip().lower() == "cat":
                cat_ids.add(class_id)

    return cat_ids


def frame_has_cat(result, cat_ids: Set[int]) -> tuple[bool, float]:
    """Check if a result contains at least one cat and return top cat confidence."""
    if result.boxes is None or len(result.boxes) == 0:
        return False, 0.0

    top_conf = 0.0
    found = False

    class_ids = result.boxes.cls.tolist()
    confidences = result.boxes.conf.tolist()

    for cls_id, conf in zip(class_ids, confidences):
        if int(cls_id) in cat_ids:
            found = True
            top_conf = max(top_conf, float(conf))

    return found, top_conf


def detect_image(args: argparse.Namespace) -> None:
    model = YOLO(args.model)
    cat_ids = get_cat_class_ids(model.names)

    if not cat_ids:
        raise RuntimeError(
            "The loaded model has no class named 'cat'. Use weights that include a cat class."
        )

    result = model.predict(
        source=args.source,
        conf=args.conf,
        imgsz=args.imgsz,
        verbose=False,
    )[0]
    found, top_conf = frame_has_cat(result, cat_ids)

    print(f"cat_found={found}")
    print(f"top_cat_confidence={top_conf:.4f}")

    if args.save:
        annotated = result.plot()
        cv2.imwrite(args.save, annotated)
        print(f"saved_annotated_image={args.save}")


def detect_video(args: argparse.Namespace) -> None:
    model = YOLO(args.model)
    cat_ids = get_cat_class_ids(model.names)
    trigger_ids = get_snapshot_trigger_class_ids(model.names)

    if not cat_ids:
        raise RuntimeError(
            "The loaded model has no class named 'cat'. Use weights that include a cat class."
        )
    if not trigger_ids:
        raise RuntimeError(
            "The loaded model has no supported snapshot trigger classes. Use compatible weights."
        )

    source, display_source = resolve_video_source(args)
    cap = cv2.VideoCapture(source)
    if args.capture_buffer_size > 0:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, float(args.capture_buffer_size))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video source: {display_source}")

    max_consecutive_read_failures = 15
    max_reconnect_attempts = 20
    read_retry_sleep_s = 0.05
    reconnect_sleep_s = 1.0

    writer = None
    if args.output:
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30.0
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(args.output, fourcc, fps, (width, height))

    window_name = "Cat Detector"
    screen_width, screen_height = get_screen_size()
    display_max_width = max(320, screen_width - 80)
    display_max_height = max(240, screen_height - 140)

    if args.display:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    if args.snapshot_dir:
        os.makedirs(args.snapshot_dir, exist_ok=True)

    if args.telegram_send:
        if args.telegram_token and args.telegram_chat_id:
            write_telegram_config(args.telegram_config, args.telegram_token, args.telegram_chat_id)
        elif args.telegram_token and not args.telegram_chat_id and not os.path.isfile(args.telegram_config):
            print(
                "telegram_send_warning=TELEGRAM_CHAT_ID is missing and telegram config file was not found"
            )

    snapshot_queue: Queue[tuple[str, object, bool] | None] | None = None
    snapshot_worker: threading.Thread | None = None

    def log_timing(label: str, started_at: float) -> None:
        if args.timing_log:
            elapsed_ms = (time.perf_counter() - started_at) * 1000.0
            print(f"timing_{label}_ms={elapsed_ms:.1f}")

    if args.snapshot_dir:
        snapshot_queue = Queue()

        def _snapshot_worker() -> None:
            while True:
                item = snapshot_queue.get()
                try:
                    if item is None:
                        return

                    snapshot_path, snapshot_image, trigger_detected = item

                    save_started_at = time.perf_counter()
                    cv2.imwrite(snapshot_path, snapshot_image)
                    log_timing("snapshot_save", save_started_at)

                    if args.telegram_send:
                        telegram_started_at = time.perf_counter()
                        send_snapshot_via_telegram(args, snapshot_path, trigger_detected)
                        log_timing("telegram_send", telegram_started_at)
                finally:
                    snapshot_queue.task_done()

        snapshot_worker = threading.Thread(target=_snapshot_worker, daemon=True)
        snapshot_worker.start()

    any_cat_seen = False
    processed_frames = 0
    last_beep_ts = 0.0
    last_snapshot_ts = 0.0
    snapshots_saved = 0
    consecutive_read_failures = 0
    reconnect_attempts = 0
    last_inference_ts = 0.0
    beep_lock = threading.Lock()
    beep_active = False

    def trigger_beep_if_needed(found: bool) -> None:
        nonlocal last_beep_ts, beep_active
        if not args.beep_on_cat or not found:
            return

        now = time.monotonic()
        if now - last_beep_ts < args.beep_cooldown:
            return

        with beep_lock:
            if beep_active:
                return
            beep_active = True
            last_beep_ts = now

        def _beep_worker() -> None:
            nonlocal beep_active
            try:
                play_beep_beep_alert()
            finally:
                with beep_lock:
                    beep_active = False

        threading.Thread(target=_beep_worker, daemon=True).start()

    try:
        while True:
            try:
                ok, frame = cap.read()
            except cv2.error as exc:
                ok, frame = False, None
                print(f"stream_read_warning={exc}")

            if not ok or frame is None or frame.size == 0:
                consecutive_read_failures += 1
                if consecutive_read_failures < max_consecutive_read_failures:
                    time.sleep(read_retry_sleep_s)
                    continue

                reconnect_attempts += 1
                print(
                    "stream_reconnect_warning="
                    f"read failures reached {consecutive_read_failures}; reconnect attempt {reconnect_attempts}/{max_reconnect_attempts}"
                )

                cap.release()
                time.sleep(reconnect_sleep_s)
                cap = cv2.VideoCapture(source)
                if args.capture_buffer_size > 0:
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, float(args.capture_buffer_size))
                if cap.isOpened():
                    consecutive_read_failures = 0
                    continue

                if reconnect_attempts >= max_reconnect_attempts:
                    print(
                        "stream_ended="
                        "maximum reconnect attempts reached after repeated read/decode failures"
                    )
                    break

                continue

            consecutive_read_failures = 0
            reconnect_attempts = 0

            if args.frame_skip > 0 and processed_frames % (args.frame_skip + 1) != 0:
                processed_frames += 1
                if args.max_frames > 0 and processed_frames >= args.max_frames:
                    break

                if args.display:
                    frame_for_display = (
                        fit_frame_to_screen(frame, display_max_width, display_max_height)
                        if args.fit_display
                        else frame
                    )
                    try:
                        cv2.imshow(window_name, frame_for_display)
                    except cv2.error as exc:
                        print(f"display_warning={exc}")
                        break
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                continue

            now = time.monotonic()
            if args.inference_interval > 0 and now - last_inference_ts < args.inference_interval:
                processed_frames += 1
                if args.max_frames > 0 and processed_frames >= args.max_frames:
                    break

                if args.display:
                    frame_for_display = (
                        fit_frame_to_screen(frame, display_max_width, display_max_height)
                        if args.fit_display
                        else frame
                    )
                    try:
                        cv2.imshow(window_name, frame_for_display)
                    except cv2.error as exc:
                        print(f"display_warning={exc}")
                        break
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                continue

            try:
                inference_started_at = time.perf_counter()
                result = model.predict(
                    source=frame,
                    conf=args.conf,
                    imgsz=args.imgsz,
                    classes=sorted(trigger_ids),
                    verbose=False,
                )[0]
                last_inference_ts = time.monotonic()
                log_timing("inference", inference_started_at)
            except Exception as exc:
                print(f"frame_inference_warning={exc}")
                continue

            found, top_conf = frame_has_cat(result, cat_ids)
            trigger_found = frame_has_any_class(result, trigger_ids)
            any_cat_seen = any_cat_seen or found
            trigger_beep_if_needed(found)

            annotated = result.plot()
            label = "CAT DETECTED" if found else "NO CAT"
            text = f"{label} | conf={top_conf:.2f}" if found else label
            draw_status_banner(annotated, text)

            should_capture_snapshot = trigger_found
            if should_capture_snapshot and args.snapshot_dir:
                now = time.monotonic()
                if now - last_snapshot_ts >= args.snapshot_cooldown:
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    milliseconds = int((time.time() % 1) * 1000)
                    filename = f"snapshot_{timestamp}_{milliseconds:03d}.jpg"
                    snapshot_path = os.path.join(args.snapshot_dir, filename)
                    last_snapshot_ts = now
                    snapshots_saved += 1
                    if snapshot_queue is not None:
                        snapshot_queue.put((snapshot_path, annotated.copy(), trigger_found))

            if writer is not None:
                try:
                    write_started_at = time.perf_counter()
                    writer.write(annotated)
                    log_timing("video_write", write_started_at)
                except cv2.error as exc:
                    print(f"video_write_warning={exc}")

            processed_frames += 1
            if args.max_frames > 0 and processed_frames >= args.max_frames:
                break

            if args.display:
                if args.fit_display:
                    frame_for_display = fit_frame_to_screen(
                        annotated, display_max_width, display_max_height
                    )
                else:
                    frame_for_display = annotated
                try:
                    cv2.imshow(window_name, frame_for_display)
                except cv2.error as exc:
                    print(f"display_warning={exc}")
                    break
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        cap.release()
        if writer is not None:
            writer.release()
        if args.display:
            cv2.destroyAllWindows()
        if snapshot_queue is not None:
            snapshot_queue.put(None)
            snapshot_queue.join()
        if snapshot_worker is not None:
            snapshot_worker.join(timeout=5.0)

    print(f"cat_seen_in_stream={any_cat_seen}")
    if args.output:
        print(f"saved_annotated_video={args.output}")
    if args.snapshot_dir:
        print(f"snapshots_saved={snapshots_saved}")
        print(f"snapshot_dir={args.snapshot_dir}")
    if args.telegram_send:
        print("telegram_send_enabled=True")


def detect_batch(args: argparse.Namespace) -> None:
    model = YOLO(args.model)
    cat_ids = get_cat_class_ids(model.names)

    if not cat_ids:
        raise RuntimeError(
            "The loaded model has no class named 'cat'. Use weights that include a cat class."
        )

    source_dir = args.source
    if not os.path.isdir(source_dir):
        raise RuntimeError(f"Batch source is not a directory: {source_dir}")

    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
    entries = sorted(os.listdir(source_dir))
    image_paths = [
        os.path.join(source_dir, name)
        for name in entries
        if os.path.isfile(os.path.join(source_dir, name))
        and os.path.splitext(name)[1].lower() in image_exts
    ]

    if not image_paths:
        print("batch_total_images=0")
        print("batch_cat_images=0")
        print("batch_no_cat_images=0")
        return

    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)

    cat_images = 0
    no_cat_images = 0

    for image_path in image_paths:
        result = model.predict(
            source=image_path,
            conf=args.conf,
            imgsz=args.imgsz,
            verbose=False,
        )[0]
        found, top_conf = frame_has_cat(result, cat_ids)

        if found:
            cat_images += 1
        else:
            no_cat_images += 1

        print(
            f"image={os.path.basename(image_path)} cat_found={found} top_cat_confidence={top_conf:.4f}"
        )

        if args.output_dir:
            out_name = f"annotated_{os.path.basename(image_path)}"
            out_path = os.path.join(args.output_dir, out_name)
            cv2.imwrite(out_path, result.plot())

    print(f"batch_total_images={len(image_paths)}")
    print(f"batch_cat_images={cat_images}")
    print(f"batch_no_cat_images={no_cat_images}")
    if args.output_dir:
        print(f"saved_annotated_batch_dir={args.output_dir}")


def build_parser() -> argparse.ArgumentParser:
    default_model_value = os.getenv("CAT_DETECTOR_MODEL", "yolo26n")
    parser = argparse.ArgumentParser(
        description="Detect whether a cat exists in an image or video stream using YOLO26 weights."
    )
    parser.add_argument(
        "--model",
        default=default_model_value,
        help=(
            "Model alias or path to weights. Supported aliases: yolo26n, yolo26s "
            "(default from CAT_DETECTOR_MODEL or yolo26n)."
        ),
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold (default: 0.25)",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Inference image size in pixels; higher can help small-object detection but is slower (default: 640)",
    )

    subparsers = parser.add_subparsers(dest="mode", required=True)

    image_parser = subparsers.add_parser("image", help="Run detection on a single image")
    image_parser.add_argument("--source", required=True, help="Path to image")
    image_parser.add_argument(
        "--save",
        default="",
        help="Optional path to save annotated output image",
    )

    video_parser = subparsers.add_parser(
        "video", help="Run detection on a video file, webcam index, or stream URL"
    )
    video_parser.add_argument(
        "--source",
        default="",
        help="Video path, stream URL (rtsp/http), or webcam index like 0",
    )
    video_parser.add_argument(
        "--capture-buffer-size",
        type=int,
        default=1,
        help="Preferred OpenCV capture buffer size for live video (default: 1, lower can reduce latency)",
    )
    video_parser.add_argument(
        "--tapo-ip",
        default="",
        help="Tapo camera IP (if set, source is built as RTSP URL)",
    )
    video_parser.add_argument(
        "--tapo-username",
        default="",
        help="Tapo camera username for RTSP",
    )
    video_parser.add_argument(
        "--tapo-password",
        default="",
        help="Tapo camera password for RTSP",
    )
    video_parser.add_argument(
        "--tapo-profile",
        choices=["main", "sub"],
        default="main",
        help="Tapo RTSP profile: main=stream1, sub=stream2 (default: main)",
    )
    video_parser.add_argument(
        "--display",
        action="store_true",
        help="Display annotated frames in a window (press q to quit)",
    )
    video_parser.add_argument(
        "--fit-display",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Fit preview to screen while preserving full frame (default: enabled)",
    )
    video_parser.add_argument(
        "--output",
        default="",
        help="Optional path to save annotated output video",
    )
    video_parser.add_argument(
        "--max-frames",
        type=int,
        default=0,
        help="Optional limit for processed frames; 0 means no limit",
    )
    video_parser.add_argument(
        "--frame-skip",
        type=int,
        default=0,
        help="Skip this many frames between inference runs in video mode (default: 0)",
    )
    video_parser.add_argument(
        "--inference-interval",
        type=float,
        default=0.0,
        help="Minimum seconds between inference runs in video mode (default: 0.0)",
    )
    video_parser.add_argument(
        "--beep-on-cat",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable beep-beep alert when a cat is detected (default: enabled)",
    )
    video_parser.add_argument(
        "--beep-cooldown",
        type=float,
        default=3.0,
        help="Minimum seconds between beep alerts (default: 3.0)",
    )
    video_parser.add_argument(
        "--snapshot-dir",
        default="snapshots",
        help="Directory for timestamped snapshots (animal detections, or periodic when --telegram-send is enabled)",
    )
    video_parser.add_argument(
        "--snapshot-cooldown",
        type=float,
        default=2.0,
        help="Minimum seconds between saved snapshots (default: 2.0)",
    )
    video_parser.add_argument(
        "--telegram-send",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Send saved snapshots using telegram-send",
    )
    video_parser.add_argument(
        "--telegram-token",
        default=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        help="Telegram bot token for telegram-send config (default from TELEGRAM_BOT_TOKEN)",
    )
    video_parser.add_argument(
        "--telegram-chat-id",
        default=os.getenv("TELEGRAM_CHAT_ID", ""),
        help="Telegram chat id for telegram-send config (default from TELEGRAM_CHAT_ID)",
    )
    video_parser.add_argument(
        "--telegram-config",
        default="telegram-send.conf",
        help="Path to telegram-send config file",
    )
    video_parser.add_argument(
        "--timing-log",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Print timing diagnostics for inference, snapshot save, telegram send, and video write",
    )

    batch_parser = subparsers.add_parser(
        "batch", help="Run detection on all images in a folder"
    )
    batch_parser.add_argument("--source", required=True, help="Path to image folder")
    batch_parser.add_argument(
        "--output-dir",
        default="",
        help="Optional folder to save annotated images",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.model = resolve_model_path(args.model)

    if args.mode == "image":
        detect_image(args)
    elif args.mode == "video":
        detect_video(args)
    elif args.mode == "batch":
        detect_batch(args)
    else:
        parser.error("Unknown mode")


if __name__ == "__main__":
    main()
