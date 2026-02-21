"""MidJourney 스타일 선택 노드."""
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from aiohttp import web as aiohttp_web
from server import PromptServer
from comfy_api.latest import io
import folder_paths
from .. import _DIR

_PLUGIN_STYLE_DIR = _DIR / "mj" / "style"
_COMFY_ROOT = Path(folder_paths.base_path)
_USER_STYLE_DIR = _COMFY_ROOT / "user" / "mj" / "style"
_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
_CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def _collect_styles() -> dict[str, Path]:
    """스타일 이름 → Path 매핑. user 경로가 plugin 경로를 덮어씀.

    디렉토리 구조: mj/style/<version_int>/<name>__<sref>.<ext>
    version_int은 정수여야 하며 (6, 7, 8 등), 정수가 아닌 폴더는 무시.
    """
    styles: dict[str, Path] = {}
    for base_dir in (_PLUGIN_STYLE_DIR, _USER_STYLE_DIR):
        if not base_dir.is_dir():
            continue
        for version_dir in sorted(base_dir.iterdir()):
            if not version_dir.is_dir():
                continue
            try:
                int(version_dir.name)
            except ValueError:
                continue
            for p in sorted(version_dir.iterdir()):
                if p.suffix.lower() not in _IMAGE_EXTS:
                    continue
                if "__" not in p.stem:
                    continue
                name = p.stem.split("__", 1)[0]
                styles[name] = p
    return styles


@PromptServer.instance.routes.get("/mj/style_image")
async def _mj_style_image_api(request):
    name = request.rel_url.query.get("name", "")
    path = _collect_styles().get(name)
    if path is None:
        return aiohttp_web.Response(status=404)
    ct = _CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream")
    return aiohttp_web.Response(body=path.read_bytes(), content_type=ct)


class MJ_StyleSelect(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        styles = _collect_styles()
        options = sorted(styles.keys()) or ["(none)"]
        return io.Schema(
            node_id="MJ_StyleSelect",
            display_name="Style Select",
            category="Midjourney/style",
            description="스타일을 선택해 sref 코드, sv(버전), 미리보기 이미지를 출력합니다.",
            inputs=[
                io.Combo.Input("style", options=options, default=options[0]),
            ],
            outputs=[
                io.String.Output(display_name="sref"),
                io.String.Output(display_name="sv"),
                io.Image.Output(display_name="preview"),
            ],
        )

    @classmethod
    def execute(cls, style) -> io.NodeOutput:
        styles = _collect_styles()
        path = styles.get(style)
        if path is None:
            return io.NodeOutput("", "7", torch.zeros(1, 64, 64, 3))

        sref = path.stem.split("__", 1)[1]
        sv = path.parent.name  # 부모 폴더명을 그대로 문자열로 사용 ("4"/"6"/"7"/"8")

        img = Image.open(path).convert("RGB")
        tensor = torch.from_numpy(
            np.array(img).astype(np.float32) / 255.0
        )[None,]

        return io.NodeOutput(sref, sv, tensor)
