from pathlib import Path
import time
import statistics
import numpy as np
import cv2
from ultralytics import YOLO
import openvino as ov


def pick_image() -> Path:
    root = Path('.')
    candidates = []
    for folder in [root / 'snapshots', root / 'Some hits, some misses', root]:
        if folder.exists():
            candidates.extend(folder.glob('*.jpg'))
            candidates.extend(folder.glob('*.jpeg'))
            candidates.extend(folder.glob('*.png'))
    if not candidates:
        raise RuntimeError('No image found for benchmark')
    return sorted(candidates)[0]


def prep_for_ov(img_bgr, size=640):
    resized = cv2.resize(img_bgr, (size, size), interpolation=cv2.INTER_LINEAR)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    nchw = np.transpose(rgb, (2, 0, 1))[None, ...].astype(np.uint8)
    return nchw


def bench_ultralytics(model_path, image_path, runs=20, warmup=3, device='cpu'):
    model = YOLO(str(model_path))
    for _ in range(warmup):
        model.predict(source=str(image_path), imgsz=640, device=device, verbose=False)
    times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        model.predict(source=str(image_path), imgsz=640, device=device, verbose=False)
        times.append((time.perf_counter() - t0) * 1000.0)
    return times


def bench_ov_runtime(xml_path, input_tensor, device='CPU', runs=300, warmup=20):
    core = ov.Core()
    compiled = core.compile_model(str(xml_path), device)
    req = compiled.create_infer_request()
    input_layer = compiled.input(0)

    for _ in range(warmup):
        req.infer({input_layer: input_tensor})

    times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        req.infer({input_layer: input_tensor})
        times.append((time.perf_counter() - t0) * 1000.0)
    return times


def summarize(name, times):
    avg = statistics.mean(times)
    med = statistics.median(times)
    mn = min(times)
    mx = max(times)
    fps = 1000.0 / avg
    print(f'{name}_avg_ms={avg:.2f}')
    print(f'{name}_median_ms={med:.2f}')
    print(f'{name}_min_ms={mn:.2f}')
    print(f'{name}_max_ms={mx:.2f}')
    print(f'{name}_fps_est={fps:.2f}')
    return avg


img = pick_image()
print(f'benchmark_image={img.as_posix()}')

img_bgr = cv2.imread(str(img))
if img_bgr is None:
    raise RuntimeError(f'Failed to read image: {img}')
input_tensor = prep_for_ov(img_bgr, size=640)

print('--- Ultralytics end-to-end ---')
pt_cpu = bench_ultralytics('yolo26n.pt', img, runs=30, warmup=5, device='cpu')
ov_cpu_ulti = bench_ultralytics('yolo26n_openvino_model', img, runs=30, warmup=5, device='cpu')

pt_avg = summarize('pytorch_cpu_e2e', pt_cpu)
ov_cpu_ulti_avg = summarize('openvino_cpu_e2e', ov_cpu_ulti)
print(f'openvino_cpu_vs_pytorch_speedup_x={pt_avg / ov_cpu_ulti_avg:.2f}')

print('--- OpenVINO Runtime infer-only ---')
xml = Path('yolo26n_openvino_model/yolo26n.xml')
if not xml.exists():
    raise RuntimeError('OpenVINO XML model missing: yolo26n_openvino_model/yolo26n.xml')

ov_cpu = bench_ov_runtime(xml, input_tensor, device='CPU', runs=400, warmup=40)
ov_gpu = bench_ov_runtime(xml, input_tensor, device='GPU', runs=400, warmup=40)

ov_cpu_avg = summarize('ov_runtime_cpu_infer', ov_cpu)
ov_gpu_avg = summarize('ov_runtime_gpu_infer', ov_gpu)
print(f'ov_runtime_gpu_vs_cpu_speedup_x={ov_cpu_avg / ov_gpu_avg:.2f}')
