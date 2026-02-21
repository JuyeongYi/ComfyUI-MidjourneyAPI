"""ImagineV7Params / SaveImagineParams / LoadImagineParams — 파라미터 노드."""

from __future__ import annotations

import torch
from comfy_api.latest import io

from .const import *
from ..utils import image_tensor_to_temp_file, list_presets, load_preset, save_preset

# 커스텀 타입
MJ_PARAMS       = io.Custom("MJ_PARAMS")
MJ_VIDEO_PARAMS = io.Custom("MJ_VIDEO_PARAMS")
MJ_JOB_ID       = io.Custom("MJ_JOB_ID")


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
                io.Combo.Input("quality", options=QUALITY_OPTIONS, default=QUALITY_OPTIONS[0]),
                io.Boolean.Input("raw", default=False),
                io.Boolean.Input("tile", default=False),
                io.Boolean.Input("draft", default=False),
                io.Combo.Input("mode", options=list(SpeedMode), default=SpeedMode.FAST),
                io.Combo.Input("visibility", options=VISIBILITY_OPTIONS,
                               default="default", tooltip="공개/비공개 설정"),
                io.Combo.Input("personalize", options=list(PersonalizeMode), default=PersonalizeMode.OFF,
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
                io.String.Input("sv", display_name="Style Version", default="",
                                optional=True,
                                tooltip=f"sref 코드가 생성된 MJ 버전. 허용값: {', '.join(SV_OPTIONS)}. 미지정 시 MJ가 자동 판단. sv=8은 현재 미지원"),
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
                image=None, iw=None, sref=None, sw=None, sv=None, oref=None, ow=None) -> io.NodeOutput:
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

        # 이미지 프롬프트 — image가 있을 때만 iw 포함
        if image is not None:
            params["image"] = image_tensor_to_temp_file(image)
            if iw is not None:
                params["iw"] = iw

        # sref — 이미지 텐서 → 임시 파일 변환, 문자열 → 그대로 사용
        # sref 없으면 sw/sv 모두 무시. sref가 이미지면 sv 무시.
        if sref is not None and sref != "":
            if isinstance(sref, torch.Tensor):
                params["sref"] = image_tensor_to_temp_file(sref)
                # 이미지 sref는 코드 버전 개념이 없으므로 sv 무시
            else:
                params["sref"] = str(sref)
                if sv:
                    if sv not in SV_OPTIONS:
                        raise ValueError(f"sv 허용값: {SV_OPTIONS}, 입력값: {sv!r}")
                    params["sv"] = int(sv)
            if sw is not None:
                params["sw"] = sw

        # oref — sref와 동일한 패턴
        if oref is not None and oref != "":
            if isinstance(oref, torch.Tensor):
                params["oref"] = image_tensor_to_temp_file(oref)
            else:
                params["oref"] = str(oref)
            if ow is not None:
                params["ow"] = ow

        # personalize 3가지 상태 처리
        if personalize == "default":
            params["personalize"] = ""
        elif personalize == "custom" and personalize_code:
            params["personalize"] = personalize_code

        return io.NodeOutput(params)


class SaveImagineParams(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MJ_SaveImagineParams",
            display_name="Save Imagine Params",
            category="Midjourney/params",
            description="파라미터를 JSON 프리셋으로 저장합니다.",
            is_output_node=True,
            inputs=[
                MJ_PARAMS.Input("params"),
                io.String.Input("name", default="my_preset"),
            ],
            outputs=[
                MJ_PARAMS.Output(display_name="params"),
            ],
        )

    @classmethod
    def execute(cls, params, name) -> io.NodeOutput:
        save_preset(name, params)
        return io.NodeOutput(params)


class LoadImagineParams(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        presets = list_presets() or ["(none)"]
        return io.Schema(
            node_id="MJ_LoadImagineParams",
            display_name="Load Imagine Params",
            category="Midjourney/params",
            description="JSON 프리셋에서 파라미터를 로드합니다.",
            inputs=[
                io.Combo.Input("name", options=presets),
            ],
            outputs=[
                MJ_PARAMS.Output(display_name="params"),
            ],
        )

    @classmethod
    def execute(cls, name) -> io.NodeOutput:
        params = load_preset(name)
        return io.NodeOutput(params)


class VideoParams(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MJ_VideoParams",
            display_name="Video Params",
            category="Midjourney/params",
            description="비디오 생성 파라미터를 설정합니다.",
            inputs=[
                io.Combo.Input("motion", options=list(MotionIntensity), optional=True,
                               tooltip="모션 강도 (미연결 시 MJ 기본값)"),
                io.Combo.Input("resolution", options=list(VideoResolution),
                               default=VideoResolution.R480),
                io.Int.Input("batch_size", default=1, min=1, max=4,
                             tooltip="생성할 비디오 변형 수 (--bs)"),
                io.Combo.Input("mode", options=list(SpeedMode), default=SpeedMode.FAST),
                io.Boolean.Input("stealth", default=False, tooltip="비공개 생성 (Stealth 모드)"),
            ],
            outputs=[
                MJ_VIDEO_PARAMS.Output(display_name="video_params"),
            ],
        )

    @classmethod
    def execute(cls, motion, resolution, batch_size, mode, stealth) -> io.NodeOutput:
        params = {
            "motion": motion,
            "resolution": resolution,
            "batch_size": batch_size,
            "mode": mode,
            "stealth": stealth,
        }
        return io.NodeOutput(params)
