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
            description="Midjourney V7 이미지 생성 파라미터. 미드저니 공식 파라미터(ar, stylize, chaos, seed 등)는 docs.midjourney.com 참고. 이 노드에서 특별히 지원하는 기능: personalize 3단계 모드(off/default/custom), sref·oref에 이미지 텐서 직접 입력 가능.",
            inputs=[
                io.Int.Input("ar_w", display_name="AR Width", default=1, min=1, max=21,
                             tooltip="종횡비 가로. AR Height와 함께 --ar W:H 로 전달됩니다 (예: 16:9의 경우 16)"),
                io.Int.Input("ar_h", display_name="AR Height", default=1, min=1, max=21,
                             tooltip="종횡비 세로 (예: 16:9의 경우 9)"),
                io.Int.Input("stylize", default=100, min=0, max=1000,
                             tooltip="--stylize. 낮을수록 프롬프트에 충실, 높을수록 MJ 고유 스타일 강화 (0–1000)"),
                io.Int.Input("chaos", default=0, min=0, max=100,
                             tooltip="--chaos. 결과물의 다양성과 예측 불가성 (0–100)"),
                io.Int.Input("weird", default=0, min=0, max=3000,
                             tooltip="--weird. 실험적·비정형적 미학 유도 (0–3000)"),
                io.Int.Input("seed", default=0, min=0, max=4294967295, control_after_generate=True,
                             tooltip="--seed. 같은 프롬프트+시드는 동일한 결과를 생성합니다"),
                io.Combo.Input("quality", options=QUALITY_OPTIONS, default=QUALITY_OPTIONS[0],
                               tooltip="--quality. 렌더링 품질: 1/2/4. 숫자 클수록 디테일↑ 속도↓"),
                io.Boolean.Input("raw", default=False,
                                 tooltip="--style raw. MJ 기본 스타일화를 최소화해 프롬프트에 더 충실한 결과를 생성합니다"),
                io.Boolean.Input("tile", default=False,
                                 tooltip="--tile. 반복 가능한 타일 패턴 이미지를 생성합니다"),
                io.Boolean.Input("draft", default=False,
                                 tooltip="--draft. 빠른 저품질 초안 생성. 구도 확인용으로 사용합니다"),
                io.Combo.Input("mode", options=list(SpeedMode), default=SpeedMode.FAST,
                               tooltip="생성 속도 모드. fast / relax / turbo"),
                io.Combo.Input("visibility", options=VISIBILITY_OPTIONS,
                               default="default", tooltip="공개/비공개 설정. default: 계정 설정 따름 / stealth: 비공개 / public: 공개"),
                io.Combo.Input("personalize", options=list(PersonalizeMode), default=PersonalizeMode.OFF,
                               tooltip="개인화 모드. off: 비활성 / default: 계정 기본 코드로 --p 전달 / custom: 아래 코드를 --p 값으로 사용"),
                io.String.Input("personalize_code", default="",
                                tooltip="custom 모드에서 사용할 개인화 코드 (예: 8ul18pe). off/default 모드에서는 무시됩니다"),
                io.Image.Input("image", optional=True, tooltip="이미지 프롬프트"),
                io.Float.Input("iw", display_name="Image Weight", default=1.0, min=0.0, max=3.0,
                               optional=True),
                io.MultiType.Input(
                    io.String.Input("sref", display_name="Style Ref", default="", optional=True,
                                    tooltip="스타일 레퍼런스. sref 코드·URL 문자열 또는 이미지 텐서를 직접 연결할 수 있습니다"),
                    types=[io.Image],
                ),
                io.String.Input("sv", display_name="Style Version", default="",
                                optional=True,
                                tooltip=f"sref 코드가 생성된 MJ 버전 (허용값: {', '.join(SV_OPTIONS)}). 미지정 시 MJ가 자동 판단. 이미지 sref에는 무시됩니다"),
                io.Int.Input("sw", display_name="Style Weight", default=100, min=0, max=1000,
                             optional=True,
                             tooltip="--sw. 스타일 레퍼런스 반영 강도 (0–1000). sref 연결 시에만 유효합니다"),
                io.MultiType.Input(
                    io.String.Input("oref", display_name="Omni Ref", default="", optional=True,
                                    tooltip="오브젝트·캐릭터 레퍼런스. 이미지 URL 또는 이미지 텐서를 직접 연결할 수 있습니다 (sref 코드와 달리 URL만 허용)"),
                    types=[io.Image],
                ),
                io.Int.Input("ow", display_name="Omni Weight", default=100, min=1, max=1000,
                             optional=True,
                             tooltip="--ow. 오브젝트 레퍼런스 반영 강도 (1–1000). oref 연결 시에만 유효합니다"),
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
            description="Animate / AnimateFromImage / ExtendVideo 노드에 연결하는 비디오 생성 파라미터. batch_size로 여러 변형을 동시에 생성하고 Load Video의 batch_index로 선택합니다.",
            inputs=[
                io.Combo.Input("motion", options=list(MotionIntensity), optional=True,
                               tooltip="모션 강도: low / high. 미연결 시 MJ 기본값 적용"),
                io.Combo.Input("resolution", options=list(VideoResolution),
                               default=VideoResolution.R480,
                               tooltip="비디오 해상도: 480 / 720"),
                io.Int.Input("batch_size", default=1, min=1, max=4,
                             tooltip="생성할 비디오 변형 수 (1–4). Load Video의 batch_index로 특정 변형을 선택합니다"),
                io.Combo.Input("mode", options=list(SpeedMode), default=SpeedMode.FAST,
                               tooltip="생성 속도 모드. fast / relax / turbo"),
                io.Boolean.Input("stealth", default=False, tooltip="비공개 생성 (Stealth 모드). 미드저니 갤러리에 노출되지 않습니다"),
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
