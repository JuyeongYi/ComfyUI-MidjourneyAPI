"""ComfyUI-MidJourney 노드 공용 유틸리티."""

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
# 클라이언트 싱글톤
# ---------------------------------------------------------------------------

_client: MidjourneyClient | None = None


def get_client() -> MidjourneyClient:
    global _client
    if _client is None:
        _client = MidjourneyClient(env_path=str(_ENV_PATH))
    return _client


# ---------------------------------------------------------------------------
# 진행률 표시와 함께 폴링
# ---------------------------------------------------------------------------


def poll_with_progress(
    job: Job,
    poll_interval: float = 5,
    timeout: float = 600,
    **_kwargs,
) -> Job:
    """Job 상태를 폴링하고, 완료 시 ComfyUI에 100% 진행률을 보고합니다."""
    if not job.id:
        raise RuntimeError("Job 제출 실패: API에서 빈 job ID가 반환되었습니다")

    client = get_client()
    pbar = comfy.utils.ProgressBar(1)
    start = time.time()

    while True:
        if time.time() - start >= timeout:
            from midjourney_api.exceptions import MidjourneyError
            raise MidjourneyError(f"Job {job.id}이(가) {timeout}초 후 타임아웃되었습니다")

        completed = client._api.get_job_status(job.id)
        if completed is not None:
            completed.status = "completed"
            completed.progress = 100
            completed.image_urls = [completed.cdn_url(i) for i in range(4)]
            pbar.update_absolute(1)
            return completed

        time.sleep(poll_interval)


# ---------------------------------------------------------------------------
# 이미지 헬퍼
# ---------------------------------------------------------------------------


def download_and_load_images(
    job: Job,
    indices: list[int] | None = None,
) -> torch.Tensor:
    """Job 이미지를 메모리에 다운로드하고 [N,H,W,C] float32 텐서를 반환합니다."""
    client = get_client()
    data_list = client.download_images_bytes(job, size=1024, indices=indices)
    tensors: list[torch.Tensor] = []
    for data in data_list:
        img = Image.open(BytesIO(data)).convert("RGB")
        arr = np.array(img, dtype=np.float32) / 255.0
        tensors.append(torch.from_numpy(arr).unsqueeze(0))  # [1,H,W,C] 형태
    return torch.cat(tensors, dim=0)  # [N,H,W,C] 형태


def try_download_all(
    job: Job,
) -> list[torch.Tensor | None]:
    """인덱스 0-3 다운로드를 시도합니다. 4개의 텐서 리스트를 반환하며, 실패 시 None입니다."""
    results: list[torch.Tensor | None] = []
    for i in range(4):
        try:
            t = download_and_load_images(job, indices=[i])
            results.append(t)
        except Exception:
            results.append(None)
    if not any(r is not None for r in results):
        raise RuntimeError(f"Job {job.id}에서 이미지를 찾을 수 없습니다")
    return results


def video_bytes_to_video_input(data: bytes):
    """Raw MP4 bytes → ComfyUI VideoInput (메모리 내, 디스크 I/O 없음)."""
    from comfy_api.latest._input_impl.video_types import VideoFromFile
    return VideoFromFile(BytesIO(data))


def image_tensor_to_temp_file(image: torch.Tensor) -> str:
    """단일 IMAGE 텐서 [1,H,W,C]를 임시 .png 파일 경로로 변환합니다."""
    arr = (image.squeeze(0).cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    fd, path = tempfile.mkstemp(suffix=".png", prefix="mj_img_")
    os.close(fd)
    img.save(path)
    return path


# ---------------------------------------------------------------------------
# 콘솔 로깅
# ---------------------------------------------------------------------------

_RST = "\033[0m"
_BOLD = "\033[1m"
_GRAY = "\033[90m"
_C1 = "\033[36m"  # 청록색 — 파라미터 이름 (홀수)
_C2 = "\033[33m"  # 황색 — 파라미터 이름 (짝수)


_SHORT = {
    "stylize": "s", "chaos": "c", "weird": "w", "quality": "q",
    "seed": "seed", "raw": "raw", "tile": "tile", "draft": "draft",
    "visibility": "vis", "personalize": "p", "source": "src",
    "index": "idx", "direction": "dir", "strong": "strong",
    "type": "type", "no": "no", "image": "img", "iw": "iw",
    "sref": "sref", "sw": "sw", "oref": "oref", "ow": "ow",
    "sv": "sv", "motion": "motion", "resolution": "res",
}


def log_job(action: str, job_id: str, prompt: str = "", mode: str = "", **params):
    """컬러 job 정보를 콘솔에 출력합니다."""
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
# 프리셋 입출력
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
