"""Shared utilities for ComfyUI-MidJourney nodes."""

from __future__ import annotations

import json
import os
import tempfile
import time
from io import BytesIO
from pathlib import Path

import numpy as np
import torch
from PIL import Image

import comfy.utils
from midjourney_api import MidjourneyClient
from midjourney_api.models import Job

_DIR = Path(__file__).parent
_ENV_PATH = _DIR.parent.parent / ".env"  # ComfyUI root
_PRESETS_DIR = _DIR / "presets"

# ---------------------------------------------------------------------------
# Client singleton
# ---------------------------------------------------------------------------

_client: MidjourneyClient | None = None


def get_client() -> MidjourneyClient:
    global _client
    if _client is None:
        _client = MidjourneyClient(env_path=str(_ENV_PATH))
    return _client


# ---------------------------------------------------------------------------
# Polling with progress
# ---------------------------------------------------------------------------


def poll_with_progress(
    job: Job,
    poll_interval: float = 5,
    timeout: float = 600,
    **_kwargs,
) -> Job:
    """Poll job status, report 100% to ComfyUI on completion."""
    if not job.id:
        raise RuntimeError("Job submission failed: empty job ID returned from API")

    client = get_client()
    pbar = comfy.utils.ProgressBar(1)
    start = time.time()

    while True:
        if time.time() - start >= timeout:
            from midjourney_api.exceptions import MidjourneyError
            raise MidjourneyError(f"Job {job.id} timed out after {timeout}s")

        completed = client._api.get_job_status(job.id)
        if completed is not None:
            completed.status = "completed"
            completed.progress = 100
            completed.image_urls = [completed.cdn_url(i) for i in range(4)]
            pbar.update_absolute(1)
            return completed

        time.sleep(poll_interval)


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------


def download_and_load_images(
    job: Job,
    size: int = 640,
    indices: list[int] | None = None,
) -> torch.Tensor:
    """Download job images in memory, return [N,H,W,C] float32 tensor."""
    client = get_client()
    data_list = client.download_images_bytes(job, size=size, indices=indices)
    tensors: list[torch.Tensor] = []
    for data in data_list:
        img = Image.open(BytesIO(data)).convert("RGB")
        arr = np.array(img, dtype=np.float32) / 255.0
        tensors.append(torch.from_numpy(arr).unsqueeze(0))  # [1,H,W,C]
    return torch.cat(tensors, dim=0)  # [N,H,W,C]


def try_download_all(
    job: Job,
    size: int = 1024,
) -> list[torch.Tensor | None]:
    """Try downloading indices 0-3. Returns list of 4 tensors (None if failed)."""
    results: list[torch.Tensor | None] = []
    for i in range(4):
        try:
            t = download_and_load_images(job, size=size, indices=[i])
            results.append(t)
        except Exception:
            results.append(None)
    if not any(r is not None for r in results):
        raise RuntimeError(f"No images found for job {job.id}")
    return results


def image_tensor_to_temp_file(image: torch.Tensor) -> str:
    """Convert a single IMAGE tensor [1,H,W,C] to a temp .png file path."""
    arr = (image.squeeze(0).cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    fd, path = tempfile.mkstemp(suffix=".png", prefix="mj_img_")
    os.close(fd)
    img.save(path)
    return path


# ---------------------------------------------------------------------------
# Console logging
# ---------------------------------------------------------------------------

_RST = "\033[0m"
_BOLD = "\033[1m"
_GRAY = "\033[90m"
_C1 = "\033[36m"  # cyan — 파라미터 이름 (홀수)
_C2 = "\033[33m"  # yellow — 파라미터 이름 (짝수)


_SHORT = {
    "stylize": "s", "chaos": "c", "weird": "w", "quality": "q",
    "seed": "seed", "raw": "raw", "tile": "tile", "draft": "draft",
    "visibility": "vis", "personalize": "p", "source": "src",
    "index": "idx", "direction": "dir", "strong": "strong",
    "type": "type", "no": "no", "image": "img", "iw": "iw",
    "sref": "sref", "sw": "sw", "oref": "oref", "ow": "ow",
}


def log_job(action: str, job_id: str, prompt: str = "", mode: str = "", **params):
    """Print colored job info to console."""
    print(f"{_BOLD}[MJ] {action}{_RST}  job={_GRAY}{job_id}{_RST}  mode={_GRAY}{mode}{_RST}")
    if prompt:
        print(f"  {_BOLD}Prompt:{_RST} {_BOLD}{prompt}{_RST}")
    for i, (k, v) in enumerate(params.items()):
        color = _C1 if i % 2 == 0 else _C2
        short = _SHORT.get(k, k)
        print(f"  {color}{short}{_RST}={_GRAY}{v}{_RST}", end="")
    if params:
        print()


# ---------------------------------------------------------------------------
# Preset I/O
# ---------------------------------------------------------------------------


def save_preset(name: str, params: dict) -> Path:
    _PRESETS_DIR.mkdir(parents=True, exist_ok=True)
    path = _PRESETS_DIR / f"{name}.json"
    path.write_text(json.dumps(params, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_preset(name: str) -> dict:
    path = _PRESETS_DIR / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def list_presets() -> list[str]:
    _PRESETS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(p.stem for p in _PRESETS_DIR.glob("*.json"))
