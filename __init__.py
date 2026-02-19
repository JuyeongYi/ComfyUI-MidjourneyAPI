"""ComfyUI-MidJourney: Midjourney image generation nodes for ComfyUI."""

from pathlib import Path

from dotenv import load_dotenv

_DIR = Path(__file__).parent
_COMFYUI_ROOT = _DIR.parent.parent  # custom_nodes/<this> → ComfyUI root
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
    SaveImagineParams,
)
from .node_keywords import KEYWORD_NODES
from .node_keyword_join import MidJourneyKeywordJoin
from .node_style import MJ_StyleSelect

WEB_DIRECTORY = "./web"

_NODES = [
    ImagineV7Params,
    SaveImagineParams,
    LoadImagineParams,
    MidJourneyImagine,
    MidJourneyVary,
    MidJourneyUpscale,
    MidJourneyPan,
    MidJourneyDownload,
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
