"""ComfyUI-MidJourney: ComfyUI용 Midjourney 이미지 생성 노드."""

from pathlib import Path

from dotenv import load_dotenv

_DIR = Path(__file__).parent
_COMFYUI_ROOT = _DIR.parent.parent  # custom_nodes/<this> → ComfyUI 루트
load_dotenv(_COMFYUI_ROOT / ".env")

from comfy_api.latest import ComfyExtension, io
from typing_extensions import override

from .nodes import (
    ImagineV7Params,
    LoadImagineParams,
    MidJourneyDownload,
    MidJourneyImagine,
    MidJourneyPan,
    MidJourneyUpscale,
    MidJourneyVary,
    MidJourneyRemix,
    SaveImagineParams,
    VideoParams,
    KEYWORD_NODES,
    MidJourneyKeywordJoin,
    MJ_StyleSelect,
    MidJourneyAnimate,
    MidJourneyAnimateFromImage,
    MidJourneyExtendVideo,
    MidJourneyLoadVideo,
)

WEB_DIRECTORY = "./web"

_NODES = [
    ImagineV7Params,
    SaveImagineParams,
    LoadImagineParams,
    MidJourneyImagine,
    MidJourneyVary,
    MidJourneyRemix,
    MidJourneyUpscale,
    MidJourneyPan,
    MidJourneyDownload,
    VideoParams,
    MidJourneyAnimate,
    MidJourneyAnimateFromImage,
    MidJourneyExtendVideo,
    MidJourneyLoadVideo,
    *KEYWORD_NODES,
    MidJourneyKeywordJoin,
    MJ_StyleSelect,
]


class MidJourneyExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return _NODES


async def comfy_entrypoint() -> MidJourneyExtension:
    return MidJourneyExtension()
