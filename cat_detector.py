import argparse
import ctypes
import math
import os
import threading
from queue import Queue
import subprocess
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
    "yolo26n_ov": "yolo26n_openvino_model",
    "yolo26s_ov": "yolo26s_openvino_model",
}


def normalize_inference_device(device_value: str) -> str:
    """Normalize CLI device value used for model.predict device routing."""
    normalized = (device_value or "").strip()
    if not normalized:
        return "auto"
    lowered = normalized.lower()
    return "auto" if lowered == "auto" else normalized


def resolve_predict_device_arg(device_value: str):
    """Return device argument for Ultralytics predict call, using auto-routing when requested."""
    return None if device_value == "auto" else device_value


def print_inference_runtime_info(args: argparse.Namespace, model: YOLO) -> None:
    """Print selected and effective inference device/backend hints for diagnostics."""
    print(f"inference_device_requested={args.device}")
    predictor = getattr(model, "predictor", None)
    if predictor is not None:
        effective_device = getattr(predictor, "device", None)
        if effective_device is not None:
            print(f"inference_device_effective={effective_device}")


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

    # Place banner at upper right
    x2 = frame.shape[1] - margin_x
    x1 = x2 - (text_width + 16)
    y1 = margin_y
    y2 = y1 + text_height + baseline + 10

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

def draw_watermark_q(frame):
    """Draw current window control hints at bottom left."""
    watermark = "Controls: q quit | h options | r rec on/off | s snapshot"
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 1.2
    thickness = 2
    margin_x = 14
    margin_y = 34
    text_size, baseline = cv2.getTextSize(watermark, font, scale, thickness)
    text_width, text_height = text_size
    x = margin_x
    y = frame.shape[0] - margin_y
    cv2.rectangle(
        frame,
        (x - 6, y - text_height - baseline - 6),
        (x + text_width + 6, y + baseline + 6),
        (200, 240, 255),
        thickness=-1,
    )
    cv2.putText(
        frame,
        watermark,
        (x, y),
        font,
        scale,
        (0, 0, 200),
        thickness,
        lineType=cv2.LINE_AA,
    )


def draw_recording_indicator(frame, is_recording: bool) -> None:
    """Draw 'REC' indicator at bottom left when recording is active."""
    if not is_recording:
        return

    rec_text = "REC"
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 2.0
    thickness = 3
    margin_x = 14
    margin_y = 170
    text_size, baseline = cv2.getTextSize(rec_text, font, scale, thickness)
    text_width, text_height = text_size
    x = margin_x
    y = frame.shape[0] - margin_y

    # Smooth pulse (sine wave) avoids harsh frame-by-frame flicker.
    pulse_hz = 1.2
    phase = time.monotonic() * 2.0 * math.pi * pulse_hz
    pulse = 0.5 + 0.5 * (1.0 + math.sin(phase)) * 0.5
    alpha = 0.35 + 0.55 * pulse

    x1 = x - 8
    y1 = y - text_height - baseline - 8
    x2 = x + text_width + 8
    y2 = y + baseline + 8

    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 255), thickness=-1)
    cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0.0, frame)

    text_intensity = int(180 + 75 * pulse)
    cv2.putText(
        frame,
        rec_text,
        (x, y),
        font,
        scale,
        (text_intensity, text_intensity, text_intensity),
        thickness,
        lineType=cv2.LINE_AA,
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


def create_video_writer_with_fallback(
    output_path: str,
    fps: float,
    frame_size: tuple[int, int],
    codec_candidates: tuple[str, ...] = ("avc1", "H264", "X264", "mp4v"),
):
    """Create a VideoWriter by trying preferred codecs in order."""
    width, height = frame_size
    if width <= 0 or height <= 0:
        return None, None, None

    safe_fps = fps if fps and fps > 0 else 30.0

    attempts: list[tuple[int | None, str, str]] = []
    if os.name == "nt":
        msmf_backend = getattr(cv2, "CAP_MSMF", None)
        if msmf_backend is not None:
            for codec in codec_candidates:
                attempts.append((msmf_backend, "CAP_MSMF", codec))

    for codec in codec_candidates:
        attempts.append((None, "default", codec))

    seen_attempts: set[tuple[int | None, str]] = set()
    for api_pref, backend_name, codec in attempts:
        key = (api_pref, codec)
        if key in seen_attempts:
            continue
        seen_attempts.add(key)
        try:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            if api_pref is None:
                writer = cv2.VideoWriter(output_path, fourcc, safe_fps, (width, height))
            else:
                writer = cv2.VideoWriter(output_path, api_pref, fourcc, safe_fps, (width, height))
            if writer.isOpened():
                return writer, codec, backend_name
            writer.release()
        except cv2.error:
            continue

    return None, None, None


def get_snapshot_trigger_class_ids(
    names: Union[dict, list], include_person: bool = True, include_bird: bool = True, include_dog: bool = True, include_bear: bool = True
) -> Set[int]:
    """Resolve class ids that should trigger snapshots and Telegram sends."""
    trigger_names = {
        "cat",
        "horse",
        "sheep",
        "cow",
        "elephant",
        "zebra",
        "giraffe",
    }
    if include_bear:
        trigger_names.add("bear")
    if include_dog:
        trigger_names.add("dog")
    if include_person:
        trigger_names.add("person")
    if include_bird:
        trigger_names.add("bird")

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


def extract_plot_detections(result) -> list[tuple[tuple[int, int, int, int], int, float]]:
    """Extract boxes for display reuse between inference frames."""
    if result.boxes is None or len(result.boxes) == 0:
        return []

    boxes = result.boxes.xyxy.tolist()
    classes = result.boxes.cls.tolist()
    confidences = result.boxes.conf.tolist()
    extracted: list[tuple[tuple[int, int, int, int], int, float]] = []

    for xyxy, cls_id, conf in zip(boxes, classes, confidences):
        x1, y1, x2, y2 = xyxy
        extracted.append(
            (
                (int(x1), int(y1), int(x2), int(y2)),
                int(cls_id),
                float(conf),
            )
        )

    return extracted


def draw_cached_detections(
    frame, detections: list[tuple[tuple[int, int, int, int], int, float]], names: Union[dict, list]
) -> None:
    """Draw cached detections on frames that skip inference to avoid flashing overlays."""
    for (x1, y1, x2, y2), cls_id, conf in detections:
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        if isinstance(names, dict):
            class_name = str(names.get(cls_id, cls_id))
        elif isinstance(names, Iterable):
            class_name = str(names[cls_id]) if 0 <= cls_id < len(names) else str(cls_id)
        else:
            class_name = str(cls_id)

        label = f"{class_name} {conf:.2f}"
        text_size, baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        text_w, text_h = text_size
        box_top = max(0, y1 - text_h - baseline - 8)
        box_bottom = box_top + text_h + baseline + 6
        box_right = x1 + text_w + 10
        cv2.rectangle(frame, (x1, box_top), (box_right, box_bottom), (0, 255, 0), thickness=-1)
        cv2.putText(
            frame,
            label,
            (x1 + 5, box_bottom - baseline - 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            2,
            cv2.LINE_AA,
        )


def box_iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    """Compute IoU between two xyxy boxes."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    if inter_area <= 0:
        return 0.0

    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = area_a + area_b - inter_area
    if union <= 0:
        return 0.0
    return inter_area / union


def smooth_plot_detections(
    previous: list[tuple[tuple[int, int, int, int], int, float]],
    current: list[tuple[tuple[int, int, int, int], int, float]],
    alpha: float,
    iou_threshold: float,
) -> list[tuple[tuple[int, int, int, int], int, float]]:
    """Smooth current detection boxes against previous ones to reduce visible jitter."""
    if not previous or not current:
        return current

    used_previous: set[int] = set()
    smoothed: list[tuple[tuple[int, int, int, int], int, float]] = []

    for curr_box, curr_cls, curr_conf in current:
        best_idx = -1
        best_iou = 0.0

        for idx, (prev_box, prev_cls, _prev_conf) in enumerate(previous):
            if idx in used_previous or prev_cls != curr_cls:
                continue
            iou = box_iou(curr_box, prev_box)
            if iou > best_iou:
                best_iou = iou
                best_idx = idx

        if best_idx >= 0 and best_iou >= iou_threshold:
            prev_box, _prev_cls, prev_conf = previous[best_idx]
            used_previous.add(best_idx)

            px1, py1, px2, py2 = prev_box
            cx1, cy1, cx2, cy2 = curr_box

            sx1 = int(round(px1 * (1.0 - alpha) + cx1 * alpha))
            sy1 = int(round(py1 * (1.0 - alpha) + cy1 * alpha))
            sx2 = int(round(px2 * (1.0 - alpha) + cx2 * alpha))
            sy2 = int(round(py2 * (1.0 - alpha) + cy2 * alpha))
            sconf = prev_conf * (1.0 - alpha) + curr_conf * alpha

            smoothed.append(((sx1, sy1, sx2, sy2), curr_cls, sconf))
        else:
            smoothed.append((curr_box, curr_cls, curr_conf))

    return smoothed


def prune_snapshots(snapshot_dir: str, max_files: int) -> None:
    """Delete the oldest snapshot files when the directory exceeds max_files."""
    if max_files <= 0:
        return
    try:
        entries = [
            os.path.join(snapshot_dir, f)
            for f in os.listdir(snapshot_dir)
            if os.path.isfile(os.path.join(snapshot_dir, f))
        ]
        if len(entries) <= max_files:
            return
        entries.sort(key=lambda p: os.path.getmtime(p))
        to_delete = entries[: len(entries) - max_files]
        for path in to_delete:
            try:
                os.remove(path)
            except OSError as exc:
                print(f"snapshot_prune_warning={exc}")
        print(f"snapshot_pruned={len(to_delete)}")
    except OSError as exc:
        print(f"snapshot_prune_warning={exc}")


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
        device=resolve_predict_device_arg(args.device),
        verbose=False,
    )[0]
    print_inference_runtime_info(args, model)
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
    trigger_ids = get_snapshot_trigger_class_ids(
        model.names,
        include_person=args.alert_person,
        include_bird=args.alert_bird,
        include_dog=args.alert_dog,
        include_bear=args.alert_bear,
    )

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
    writer_codec: str | None = None
    writer_init_failed = False
    output_fps = cap.get(cv2.CAP_PROP_FPS)
    if output_fps <= 0:
        output_fps = 30.0
    if args.output:
        print("video_writer_info=will initialize output writer on first processed frame")

    interactive_recording_writer = None
    interactive_recording_path: str | None = None
    interactive_recording_size: tuple[int, int] | None = None
    interactive_recording_fps = cap.get(cv2.CAP_PROP_FPS)
    if interactive_recording_fps <= 0:
        interactive_recording_fps = 30.0
    interactive_recording_codec: str | None = None
    interactive_preferred_codec: str | None = None

    def stop_interactive_recording() -> None:
        nonlocal interactive_recording_writer, interactive_recording_path, interactive_recording_size, interactive_recording_codec
        if interactive_recording_writer is None:
            return
        interactive_recording_writer.release()
        print(f"interactive_recording_stopped={interactive_recording_path}")
        interactive_recording_writer = None
        interactive_recording_path = None
        interactive_recording_size = None
        interactive_recording_codec = None

    def start_interactive_recording(frame_to_record) -> None:
        nonlocal interactive_recording_writer, interactive_recording_path, interactive_recording_size
        nonlocal interactive_recording_codec, interactive_preferred_codec
        if interactive_recording_writer is not None:
            print(f"interactive_recording_already_running={interactive_recording_path}")
            return

        height, width = frame_to_record.shape[:2]
        recordings_dir = os.path.join(os.getcwd(), "recordings")
        os.makedirs(recordings_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(recordings_dir, f"recording_{timestamp}.mp4")
        codec_candidates = ("avc1", "H264", "X264", "mp4v")
        if interactive_preferred_codec:
            codec_candidates = (interactive_preferred_codec,)
        candidate_writer, selected_codec, selected_backend = create_video_writer_with_fallback(
            output_path,
            interactive_recording_fps,
            (width, height),
            codec_candidates=codec_candidates,
        )
        if candidate_writer is None and interactive_preferred_codec:
            candidate_writer, selected_codec, selected_backend = create_video_writer_with_fallback(
                output_path,
                interactive_recording_fps,
                (width, height),
            )
        if candidate_writer is None:
            print(f"interactive_recording_warning=failed to open writer for {output_path}")
            return

        interactive_recording_writer = candidate_writer
        interactive_recording_codec = selected_codec
        interactive_preferred_codec = selected_codec
        interactive_recording_path = output_path
        interactive_recording_size = (width, height)
        print(f"interactive_recording_started={output_path}")
        print(f"interactive_recording_codec={interactive_recording_codec}")
        print(f"interactive_recording_backend={selected_backend}")

    def write_interactive_recording_frame(frame_to_record) -> None:
        if interactive_recording_writer is None:
            return

        current_size = (frame_to_record.shape[1], frame_to_record.shape[0])
        if interactive_recording_size is not None and current_size != interactive_recording_size:
            print(
                "interactive_recording_warning="
                f"frame size changed from {interactive_recording_size} to {current_size}; stopping recording"
            )
            stop_interactive_recording()
            return

        try:
            interactive_recording_writer.write(frame_to_record)
        except cv2.error as exc:
            print(f"interactive_recording_warning={exc}")
            stop_interactive_recording()

    def save_manual_snapshot(frame_to_snapshot) -> None:
        snapshots_manual_dir = os.path.join(os.getcwd(), "snapshots_manual")
        os.makedirs(snapshots_manual_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        milliseconds = int((time.time() % 1) * 1000)
        snapshot_filename = f"snapshot_{timestamp}_{milliseconds:03d}.jpg"
        snapshot_path = os.path.join(snapshots_manual_dir, snapshot_filename)
        try:
            cv2.imwrite(snapshot_path, frame_to_snapshot)
            print(f"manual_snapshot_saved={snapshot_path}")
            
            def show_snapshot_popup():
                try:
                    import tkinter as tk
                    root = tk.Tk()
                    root.title("Snapshot Saved")
                    root.attributes("-topmost", True)
                    root.geometry("300x100")
                    label = tk.Label(root, text="Snapshot saved!", font=("Arial", 16), fg="green")
                    label.pack(expand=True)
                    root.after(1500, lambda: root.destroy())
                    root.mainloop()
                except Exception:
                    pass
            
            threading.Thread(target=show_snapshot_popup, daemon=True).start()
        except cv2.error as exc:
            print(f"manual_snapshot_warning={exc}")

    window_name = "Cat Detector"
    screen_width, screen_height = get_screen_size()
    display_max_width = max(320, screen_width - 80)
    display_max_height = max(240, screen_height - 140)

    if args.display:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        # Maximize the window at startup (not fullscreen)
        try:
            cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
        except Exception:
            pass
        print("window_controls=q quit | h options | r toggle recording | s save snapshot")

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
    stop_event = threading.Event()
    quit_listener: threading.Thread | None = None

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

                    if args.snapshot_max_files > 0:
                        prune_snapshots(args.snapshot_dir, args.snapshot_max_files)

                    if args.telegram_send:
                        telegram_started_at = time.perf_counter()
                        send_snapshot_via_telegram(args, snapshot_path, trigger_detected)
                        log_timing("telegram_send", telegram_started_at)
                finally:
                    snapshot_queue.task_done()

        snapshot_worker = threading.Thread(target=_snapshot_worker, daemon=True)
        snapshot_worker.start()

    def _quit_listener() -> None:
        while not stop_event.is_set():
            try:
                command = input().strip().lower()
            except EOFError:
                return
            if command == "q":
                stop_event.set()
                return

    print("Type 'q' and press Enter to stop the stream gracefully.")
    quit_listener = threading.Thread(target=_quit_listener, daemon=True)
    quit_listener.start()

    any_cat_seen = False
    processed_frames = 0
    last_beep_ts = 0.0
    last_snapshot_ts = 0.0
    snapshots_saved = 0
    consecutive_read_failures = 0
    reconnect_attempts = 0
    last_inference_ts = 0.0
    last_status_text: str | None = None
    last_plot_detections: list[tuple[tuple[int, int, int, int], int, float]] = []
    last_plot_detections_ts = 0.0
    detection_overlay_hold_s = 0.8
    detection_smoothing_alpha = 0.35
    detection_smoothing_iou_threshold = 0.3
    beep_lock = threading.Lock()
    beep_active = False
    runtime_info_printed = False

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
            if stop_event.is_set():
                break

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
                    display_frame = frame.copy()
                    if last_plot_detections:
                        draw_cached_detections(display_frame, last_plot_detections, model.names)
                    if last_status_text is not None:
                        draw_status_banner(display_frame, last_status_text)
                    draw_watermark_q(display_frame)
                    draw_recording_indicator(display_frame, interactive_recording_writer is not None)
                    frame_for_display = (
                        fit_frame_to_screen(display_frame, display_max_width, display_max_height)
                        if args.fit_display
                        else display_frame
                    )
                    try:
                        cv2.imshow(window_name, frame_for_display)
                    except cv2.error as exc:
                        print(f"display_warning={exc}")
                        break
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        stop_event.set()
                        break
                    elif key == ord("r"):
                        if interactive_recording_writer is not None:
                            stop_interactive_recording()
                        else:
                            start_interactive_recording(display_frame)
                    elif key == ord("s"):
                        save_manual_snapshot(display_frame)
                    write_interactive_recording_frame(display_frame)
                continue

            now = time.monotonic()
            if args.inference_interval > 0 and now - last_inference_ts < args.inference_interval:
                processed_frames += 1
                if args.max_frames > 0 and processed_frames >= args.max_frames:
                    break

                if args.display:
                    display_frame = frame.copy()
                    if last_plot_detections:
                        draw_cached_detections(display_frame, last_plot_detections, model.names)
                    if last_status_text is not None:
                        draw_status_banner(display_frame, last_status_text)
                    draw_watermark_q(display_frame)
                    draw_recording_indicator(display_frame, interactive_recording_writer is not None)
                    frame_for_display = (
                        fit_frame_to_screen(display_frame, display_max_width, display_max_height)
                        if args.fit_display
                        else display_frame
                    )
                    try:
                        cv2.imshow(window_name, frame_for_display)
                    except cv2.error as exc:
                        print(f"display_warning={exc}")
                        break
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        stop_event.set()
                        break
                    elif key == ord("r"):
                        if interactive_recording_writer is not None:
                            stop_interactive_recording()
                        else:
                            start_interactive_recording(display_frame)
                    elif key == ord("s"):
                        save_manual_snapshot(display_frame)
                    write_interactive_recording_frame(display_frame)
                continue

            try:
                inference_started_at = time.perf_counter()
                result = model.predict(
                    source=frame,
                    conf=args.conf,
                    imgsz=args.imgsz,
                    device=resolve_predict_device_arg(args.device),
                    classes=sorted(trigger_ids),
                    verbose=False,
                )[0]
                if not runtime_info_printed:
                    print_inference_runtime_info(args, model)
                    runtime_info_printed = True
                last_inference_ts = time.monotonic()
                log_timing("inference", inference_started_at)
            except Exception as exc:
                print(f"frame_inference_warning={exc}")
                continue

            found, top_conf = frame_has_cat(result, cat_ids)
            trigger_found = frame_has_any_class(result, trigger_ids)
            current_detections = extract_plot_detections(result)
            current_detections = smooth_plot_detections(
                last_plot_detections,
                current_detections,
                detection_smoothing_alpha,
                detection_smoothing_iou_threshold,
            )
            now = time.monotonic()
            if current_detections:
                last_plot_detections = current_detections
                last_plot_detections_ts = now
            elif now - last_plot_detections_ts > detection_overlay_hold_s:
                last_plot_detections = []
            any_cat_seen = any_cat_seen or found
            trigger_beep_if_needed(found)

            annotated = result.plot()
            label = "CAT DETECTED" if found else "NO CAT"
            text = f"{label} | conf={top_conf:.2f}" if found else label
            last_status_text = text

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
                    writer.release()
                    writer = None
                    writer_init_failed = True
                    print("video_writer_warning=writer disabled after write failure")
            elif args.output and not writer_init_failed:
                frame_height, frame_width = annotated.shape[:2]
                writer, writer_codec, writer_backend = create_video_writer_with_fallback(
                    args.output,
                    output_fps,
                    (frame_width, frame_height),
                )
                if writer is None:
                    writer_init_failed = True
                    print(
                        "video_writer_warning="
                        f"failed to initialize output writer for {args.output}; output recording disabled"
                    )
                else:
                    print(f"video_writer_codec={writer_codec}")
                    print(f"video_writer_backend={writer_backend}")
                    try:
                        write_started_at = time.perf_counter()
                        writer.write(annotated)
                        log_timing("video_write", write_started_at)
                    except cv2.error as exc:
                        print(f"video_write_warning={exc}")
                        writer.release()
                        writer = None
                        writer_init_failed = True
                        print("video_writer_warning=writer disabled after write failure")

            processed_frames += 1
            if args.max_frames > 0 and processed_frames >= args.max_frames:
                break

            if args.display:
                display_frame = frame.copy()
                if last_plot_detections:
                    draw_cached_detections(display_frame, last_plot_detections, model.names)
                if last_status_text is not None:
                    draw_status_banner(display_frame, last_status_text)
                draw_watermark_q(display_frame)
                draw_recording_indicator(display_frame, interactive_recording_writer is not None)
                if args.fit_display:
                    frame_for_display = fit_frame_to_screen(
                        display_frame, display_max_width, display_max_height
                    )
                else:
                    frame_for_display = display_frame
                try:
                    cv2.imshow(window_name, frame_for_display)
                except cv2.error as exc:
                    print(f"display_warning={exc}")
                    break
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    stop_event.set()
                    break
                elif key == ord("r"):
                    if interactive_recording_writer is not None:
                        stop_interactive_recording()
                    else:
                        start_interactive_recording(display_frame)
                elif key == ord("s"):
                    save_manual_snapshot(display_frame)
                elif key == ord("h"):
                    # Show popup with current runtime options (custom tkinter, large font, always on top, threaded)
                    def show_options_popup(options_text):
                        try:
                            import tkinter as tk
                            from tkinter import scrolledtext
                            root = tk.Tk()
                            root.title("Cat Detector: Current Options")
                            root.attributes("-topmost", True)
                            root.resizable(True, True)
                            window_width, window_height = 600, 750
                            root.geometry(f"{window_width}x{window_height}")

                            # Dynamically determine font size to fit text
                            min_font = 10
                            max_font = 32
                            font_family = "Consolas"
                            lines = options_text.splitlines()
                            n_lines = max(1, len(lines))
                            max_line_len = max((len(line) for line in lines), default=1)

                            # Estimate font size to fit both width and height
                            # Assume average char width is 0.6 * font size, height is 1.7 * font size
                            def estimate_font_size():
                                for font_size in range(max_font, min_font - 1, -1):
                                    est_text_width = int(max_line_len * font_size * 0.6)
                                    est_text_height = int(n_lines * font_size * 1.7)
                                    if est_text_width <= window_width - 40 and est_text_height <= window_height - 40:
                                        return font_size
                                return min_font

                            font_size = estimate_font_size()
                            font = (font_family, font_size)

                            text_widget = scrolledtext.ScrolledText(root, font=font, wrap=tk.WORD)
                            text_widget.insert(tk.END, options_text)
                            text_widget.configure(state="disabled")
                            text_widget.pack(expand=True, fill="both", padx=10, pady=10)
                            def close_popup(event=None):
                                root.destroy()
                            root.bind("<Key>", close_popup)
                            root.bind("<Button-1>", close_popup)
                            root.after(100, lambda: root.focus_force())
                            root.mainloop()
                        except Exception:
                            print(options_text)
                    options = []
                    for k, v in sorted(vars(args).items()):
                        options.append(f"{k} = {v}")
                    options_text = "\n".join(options)
                    threading.Thread(target=show_options_popup, args=(options_text,), daemon=True).start()
                write_interactive_recording_frame(display_frame)
    finally:
        stop_event.set()
        cap.release()
        if writer is not None:
            writer.release()
        if interactive_recording_writer is not None:
            interactive_recording_writer.release()
        if args.display:
            cv2.destroyAllWindows()
        if snapshot_queue is not None:
            snapshot_queue.put(None)
            snapshot_queue.join()
        if snapshot_worker is not None:
            snapshot_worker.join(timeout=5.0)
        if quit_listener is not None:
            quit_listener.join(timeout=0.2)

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
    runtime_info_printed = False

    for image_path in image_paths:
        result = model.predict(
            source=image_path,
            conf=args.conf,
            imgsz=args.imgsz,
            device=resolve_predict_device_arg(args.device),
            verbose=False,
        )[0]
        if not runtime_info_printed:
            print_inference_runtime_info(args, model)
            runtime_info_printed = True
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
    default_device_value = os.getenv("CAT_DETECTOR_DEVICE", "auto")
    parser = argparse.ArgumentParser(
        description="Detect whether a cat exists in an image or video stream using YOLO26 weights."
    )
    parser.add_argument(
        "--model",
        default=default_model_value,
        help=(
            "Model alias or path to weights. Supported aliases: yolo26n, yolo26s, yolo26n_ov, yolo26s_ov "
            "(default from CAT_DETECTOR_MODEL or yolo26n). Use _ov variants for OpenVINO optimization."
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
    parser.add_argument(
        "--device",
        default=default_device_value,
        help=(
            "Inference device passed to Ultralytics (examples: auto, cpu, 0, cuda:0, GPU). "
            "Default from CAT_DETECTOR_DEVICE or auto."
        ),
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
        "--snapshot-max-files",
        type=int,
        default=int(os.getenv("SNAPSHOT_MAX_FILES", "1000")),
        help="Maximum number of files to keep in the snapshot directory; oldest deleted first (default from SNAPSHOT_MAX_FILES or 1000, 0=disabled)",
    )
    video_parser.add_argument(
        "--telegram-send",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Send saved snapshots using telegram-send",
    )
    video_parser.add_argument(
        "--alert-person",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable person as a snapshot/Telegram trigger class (default: enabled)",
    )
    video_parser.add_argument(
        "--alert-bird",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable bird as a snapshot/Telegram trigger class (default: enabled)",
    )
    video_parser.add_argument(
        "--alert-dog",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable dog as a snapshot/Telegram trigger class (default: enabled)",
    )
    video_parser.add_argument(
        "--alert-bear",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable bear as a snapshot/Telegram trigger class (default: enabled)",
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
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '?':
        # Show popup with help/options
        parser = build_parser()
        help_text = parser.format_help()
        try:
            user32 = ctypes.windll.user32
            user32.MessageBoxW(0, help_text, "Cat Detector Options", 0x40)
        except Exception:
            print(help_text)
        sys.exit(0)

    parser = build_parser()
    args = parser.parse_args()
    args.model = resolve_model_path(args.model)
    args.device = normalize_inference_device(args.device)

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
