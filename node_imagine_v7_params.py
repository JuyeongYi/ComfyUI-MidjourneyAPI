"""ImagineV7Params — Midjourney V7 파라미터 설정 노드."""

from __future__ import annotations

import torch
from comfy_api.latest import io

from .utils import image_tensor_to_temp_file

# Custom type for passing parameter dicts between nodes
MJ_PARAMS = io.Custom("MJ_PARAMS")


class ImagineV7Params(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MJ_ImagineV7Params",
            display_name="Imagine V7 Params",
            category="Midjourney/params",
            description="Midjourney V7 파라미터를 설정합니다.",
            inputs=[
                io.Int.Input("ar_w", display_name="AR Width", default=1, min=1, max=21,
                             tooltip="종횡비 가로 (예: 16:9 의 16)"),
                io.Int.Input("ar_h", display_name="AR Height", default=1, min=1, max=21,
                             tooltip="종횡비 세로 (예: 16:9 의 9)"),
                io.Int.Input("stylize", default=100, min=0, max=1000),
                io.Int.Input("chaos", default=0, min=0, max=100),
                io.Int.Input("weird", default=0, min=0, max=3000),
                io.Int.Input("seed", default=0, min=0, max=4294967295, control_after_generate=True),
                io.Combo.Input("quality", options=["1", "2", "4"], default="1"),
                io.Boolean.Input("raw", default=False),
                io.Boolean.Input("tile", default=False),
                io.Boolean.Input("draft", default=False),
                io.Combo.Input("mode", options=["fast", "relax", "turbo"], default="fast"),
                io.Combo.Input("visibility", options=["default", "stealth", "public"],
                               default="default", tooltip="공개/비공개 설정"),
                io.Combo.Input("personalize", options=["off", "default", "custom"], default="off",
                               tooltip="개인화 모드"),
                io.String.Input("personalize_code", default="",
                                tooltip="개인화 코드 (custom 모드에서만 사용)"),
                io.Image.Input("image", optional=True, tooltip="이미지 프롬프트"),
                io.Float.Input("iw", display_name="Image Weight", default=1.0, min=0.0, max=3.0,
                               optional=True),
                io.MultiType.Input(
                    io.String.Input("sref", display_name="Style Ref", default="", optional=True,
                                    tooltip="스타일 레퍼런스 (이미지 또는 URL/코드)"),
                    types=[io.Image],
                ),
                io.Int.Input("sw", display_name="Style Weight", default=100, min=0, max=1000,
                             optional=True),
                io.MultiType.Input(
                    io.String.Input("oref", display_name="Omni Ref", default="", optional=True,
                                    tooltip="옴니 레퍼런스 (이미지 또는 URL)"),
                    types=[io.Image],
                ),
                io.Int.Input("ow", display_name="Omni Weight", default=100, min=1, max=1000,
                             optional=True),
            ],
            outputs=[
                MJ_PARAMS.Output(display_name="params"),
            ],
        )

    @classmethod
    def execute(cls, ar_w, ar_h, stylize, chaos, weird, seed, quality,
                raw, tile, draft, mode, visibility, personalize, personalize_code,
                image=None, iw=None, sref=None, sw=None, oref=None, ow=None) -> io.NodeOutput:
        params: dict = {
            "ar": f"{ar_w}:{ar_h}",
            "stylize": stylize,
            "chaos": chaos,
            "weird": weird,
            "seed": seed,
            "quality": int(quality),
            "raw": raw,
            "tile": tile,
            "draft": draft,
            "mode": mode,
        }

        if visibility != "default":
            params["visibility"] = visibility

        # image prompt — include iw only when image is present
        if image is not None:
            params["image"] = image_tensor_to_temp_file(image)
            if iw is not None:
                params["iw"] = iw

        # sref — Image tensor → temp file, String → pass through
        if sref is not None and sref != "":
            if isinstance(sref, torch.Tensor):
                params["sref"] = image_tensor_to_temp_file(sref)
            else:
                params["sref"] = str(sref)
            if sw is not None:
                params["sw"] = sw

        # oref — same pattern as sref
        if oref is not None and oref != "":
            if isinstance(oref, torch.Tensor):
                params["oref"] = image_tensor_to_temp_file(oref)
            else:
                params["oref"] = str(oref)
            if ow is not None:
                params["ow"] = ow

        # personalize 3-state
        if personalize == "default":
            params["personalize"] = ""
        elif personalize == "custom" and personalize_code:
            params["personalize"] = personalize_code

        return io.NodeOutput(params)
