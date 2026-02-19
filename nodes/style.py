"""MidJourney Style Select node."""
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
    """style_name → Path. user 경로가 plugin 경로를 덮어씀."""
    styles: dict[str, Path] = {}
    for directory in (_PLUGIN_STYLE_DIR, _USER_STYLE_DIR):
        if not directory.is_dir():
            continue
        for p in sorted(directory.iterdir()):
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
            description="스타일을 선택해 sref 코드와 미리보기 이미지를 출력합니다.",
            inputs=[
                io.Combo.Input("style", options=options, default=options[0]),
            ],
            outputs=[
                io.String.Output(display_name="sref"),
                io.Image.Output(display_name="preview"),
            ],
        )

    @classmethod
    def execute(cls, style) -> io.NodeOutput:
        styles = _collect_styles()
        path = styles.get(style)
        if path is None:
            return io.NodeOutput("", torch.zeros(1, 64, 64, 3))

        sref = path.stem.split("__", 1)[1]

        img = Image.open(path).convert("RGB")
        tensor = torch.from_numpy(
            np.array(img).astype(np.float32) / 255.0
        )[None,]

        return io.NodeOutput(sref, tensor)
