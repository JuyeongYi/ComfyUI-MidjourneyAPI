"""ComfyUI-MidJourney 노드 정의 (V3 스키마)."""

from __future__ import annotations

import torch
from comfy_api.latest import io, ui
from comfy_execution.graph import ExecutionBlocker

from .const import *
from .params import MJ_JOB_ID, MJ_PARAMS, MJ_VIDEO_PARAMS
from ..utils import (
    download_and_load_images,
    get_client,
    image_tensor_to_temp_file,
    log_job,
    poll_with_progress,
    try_download_all,
    video_bytes_to_video_input,
)


def _preview_ui(images: torch.Tensor) -> ui.PreviewImage:
    return ui.PreviewImage(images)



def _enqueue_image_outputs(job, n: int = 4) -> io.NodeOutput:
    """enqueue=True일 때: 이미지 n개를 ExecutionBlocker로 차단하고 job_id만 반환."""
    blockers = [ExecutionBlocker(None)] * n
    return io.NodeOutput(*blockers, job.id)


def _enqueue_video_output(job) -> io.NodeOutput:
    """enqueue=True일 때: 비디오 노드용 — job_id만 즉시 반환."""
    return io.NodeOutput(job.id)


# ---------------------------------------------------------------------------
# 4. MidJourneyImagine — 이미지 생성
# ---------------------------------------------------------------------------

class MidJourneyImagine(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MJ_Imagine",
            display_name="MidJourney Imagine",
            category="Midjourney",
            description="Midjourney로 이미지를 생성합니다.",
            is_output_node=True,
            inputs=[
                io.String.Input("prompt", multiline=True, tooltip="이미지 프롬프트"),
                io.String.Input("no", display_name="Negative", default="",
                                multiline=True, tooltip="네거티브 프롬프트 (--no)"),
                MJ_PARAMS.Input("params", optional=True),
                io.Boolean.Input("enqueue", default=False,
                                 tooltip="True: 잡 서밋 후 즉시 반환 (폴링 없음). job_id로 나중에 MJ_Download"),
            ],
            outputs=[
                io.Image.Output(display_name="image_0"),
                io.Image.Output(display_name="image_1"),
                io.Image.Output(display_name="image_2"),
                io.Image.Output(display_name="image_3"),
                MJ_JOB_ID.Output(display_name="job_id"),
            ],
        )

    @classmethod
    def execute(cls, prompt, no, params=None, enqueue=False) -> io.NodeOutput:
        client = get_client()

        kwargs = dict(params) if params else {}
        mode = kwargs.pop("mode", "fast")

        if no:
            kwargs["no"] = no

        job = client.imagine(prompt, wait=False, mode=mode, **kwargs)
        log_job("Imagine", job.id, prompt=prompt, mode=mode, **kwargs)
        if enqueue:
            return _enqueue_image_outputs(job, n=4)
        job = poll_with_progress(job, mode=mode)
        images = download_and_load_images(job)
        return io.NodeOutput(images[0:1], images[1:2], images[2:3], images[3:4], job.id,
                             ui=_preview_ui(images))


# ---------------------------------------------------------------------------
# 5. MidJourneyVary — 변형
# ---------------------------------------------------------------------------

class MidJourneyVary(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MJ_Vary",
            display_name="MidJourney Vary",
            category="Midjourney",
            description="Midjourney 이미지 변형 (Variation).",
            is_output_node=True,
            inputs=[
                MJ_JOB_ID.Input("job_id", tooltip="원본 Job ID"),
                io.Int.Input("index", default=0, min=0, max=3,
                             tooltip="변형할 이미지 인덱스 (0-3)"),
                io.Boolean.Input("strong", default=True,
                                 tooltip="True=Strong, False=Subtle"),
                io.Combo.Input("mode", options=list(SpeedMode), default=SpeedMode.FAST),
                io.Boolean.Input("enqueue", default=False,
                                 tooltip="True: 잡 서밋 후 즉시 반환. job_id로 나중에 MJ_Download"),
            ],
            outputs=[
                io.Image.Output(display_name="image_0"),
                io.Image.Output(display_name="image_1"),
                io.Image.Output(display_name="image_2"),
                io.Image.Output(display_name="image_3"),
                MJ_JOB_ID.Output(display_name="job_id"),
            ],
        )

    @classmethod
    def execute(cls, job_id, index, strong, mode, enqueue=False) -> io.NodeOutput:
        client = get_client()
        label = "Strong" if strong else "Subtle"
        job = client.vary(job_id, index, strong=strong, wait=False, mode=mode)
        log_job(f"Vary ({label})", job.id, mode=mode, source=job_id, index=index)
        if enqueue:
            return _enqueue_image_outputs(job, n=4)
        job = poll_with_progress(job, mode=mode)
        images = download_and_load_images(job)
        return io.NodeOutput(images[0:1], images[1:2], images[2:3], images[3:4], job.id,
                             ui=_preview_ui(images))


# ---------------------------------------------------------------------------
# 6. MidJourneyRemix — 리믹스 (프롬프트 변경 변형)
# ---------------------------------------------------------------------------

class MidJourneyRemix(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MJ_Remix",
            display_name="MidJourney Remix",
            category="Midjourney",
            description="기존 이미지를 새 프롬프트로 리믹스합니다. Vary와 유사하나 프롬프트를 완전히 교체합니다.",
            is_output_node=True,
            inputs=[
                MJ_JOB_ID.Input("job_id", tooltip="원본 Job ID"),
                io.Int.Input("index", default=0, min=0, max=3,
                             tooltip="리믹스할 이미지 인덱스 (0-3)"),
                io.String.Input("prompt", multiline=True, tooltip="새 프롬프트 (기존 프롬프트를 완전히 대체)"),
                io.String.Input("no", display_name="Negative", default="",
                                multiline=True, tooltip="네거티브 프롬프트 (--no)"),
                io.Boolean.Input("strong", default=True,
                                 tooltip="True=Strong, False=Subtle"),
                MJ_PARAMS.Input("params", optional=True),
                io.Boolean.Input("enqueue", default=False,
                                 tooltip="True: 잡 서밋 후 즉시 반환. job_id로 나중에 MJ_Download"),
            ],
            outputs=[
                io.Image.Output(display_name="image_0"),
                io.Image.Output(display_name="image_1"),
                io.Image.Output(display_name="image_2"),
                io.Image.Output(display_name="image_3"),
                MJ_JOB_ID.Output(display_name="job_id"),
            ],
        )

    @classmethod
    def execute(cls, job_id, index, prompt, no, strong, params=None, enqueue=False) -> io.NodeOutput:
        client = get_client()
        kwargs = dict(params) if params else {}
        mode = kwargs.pop("mode", SpeedMode.FAST)
        stealth = kwargs.pop("visibility", None) == "stealth"
        if no:
            kwargs["no"] = no
        label = "Strong" if strong else "Subtle"
        job = client.remix(job_id, index, prompt,
                           strong=strong, wait=False, mode=mode, stealth=stealth, **kwargs)
        log_job(f"Remix ({label})", job.id, prompt=prompt, mode=mode, source=job_id, index=index, **kwargs)
        if enqueue:
            return _enqueue_image_outputs(job, n=4)
        job = poll_with_progress(job, mode=mode)
        images = download_and_load_images(job)
        return io.NodeOutput(images[0:1], images[1:2], images[2:3], images[3:4], job.id,
                             ui=_preview_ui(images))


# ---------------------------------------------------------------------------
# 7. MidJourneyUpscale — 확대
# ---------------------------------------------------------------------------

class MidJourneyUpscale(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MJ_Upscale",
            display_name="MidJourney Upscale",
            category="Midjourney",
            description="Midjourney 이미지 확대 (Upscale).",
            is_output_node=True,
            inputs=[
                MJ_JOB_ID.Input("job_id", tooltip="원본 Job ID"),
                io.Int.Input("index", default=0, min=0, max=3,
                             tooltip="확대할 이미지 인덱스 (0-3)"),
                io.Combo.Input("upscale_type",
                               options=list(UpscaleType),
                               default=UpscaleType.SUBTLE),
                io.Combo.Input("mode", options=list(SpeedMode), default=SpeedMode.FAST),
                io.Boolean.Input("enqueue", default=False,
                                 tooltip="True: 잡 서밋 후 즉시 반환. job_id로 나중에 MJ_Download"),
            ],
            outputs=[
                io.Image.Output(display_name="image"),
                MJ_JOB_ID.Output(display_name="job_id"),
            ],
        )

    @classmethod
    def execute(cls, job_id, index, upscale_type, mode, enqueue=False) -> io.NodeOutput:
        client = get_client()
        job = client.upscale(job_id, index, upscale_type=upscale_type, wait=False, mode=mode)
        log_job("Upscale", job.id, mode=mode, source=job_id, index=index, type=upscale_type)
        if enqueue:
            return _enqueue_image_outputs(job, n=1)
        job = poll_with_progress(job, mode=mode)
        images = download_and_load_images(job, indices=[0])
        return io.NodeOutput(images, job.id,
                             ui=_preview_ui(images))


# ---------------------------------------------------------------------------
# 7. MidJourneyPan — 확장
# ---------------------------------------------------------------------------

class MidJourneyPan(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MJ_Pan",
            display_name="MidJourney Pan",
            category="Midjourney",
            description="Midjourney 이미지 확장 (Pan).",
            is_output_node=True,
            inputs=[
                MJ_JOB_ID.Input("job_id", tooltip="원본 Job ID"),
                io.Int.Input("index", default=0, min=0, max=3,
                             tooltip="확장할 이미지 인덱스 (0-3)"),
                io.Combo.Input("direction",
                               options=list(PanDirection),
                               default=PanDirection.UP),
                io.String.Input("prompt", default="", multiline=True, optional=True,
                                tooltip="추가 프롬프트 (선택)"),
                io.String.Input("no", display_name="Negative", default="",
                                multiline=True, tooltip="네거티브 프롬프트 (--no)"),
                io.Combo.Input("mode", options=list(SpeedMode), default=SpeedMode.FAST),
                io.Boolean.Input("enqueue", default=False,
                                 tooltip="True: 잡 서밋 후 즉시 반환. job_id로 나중에 MJ_Download"),
            ],
            outputs=[
                io.Image.Output(display_name="image_0"),
                io.Image.Output(display_name="image_1"),
                io.Image.Output(display_name="image_2"),
                io.Image.Output(display_name="image_3"),
                MJ_JOB_ID.Output(display_name="job_id"),
            ],
        )

    @classmethod
    def execute(cls, job_id, index, direction, prompt="", no="", mode=SpeedMode.FAST, enqueue=False) -> io.NodeOutput:
        client = get_client()
        job = client.pan(job_id, index, direction=direction, prompt=_build_prompt(prompt, no), wait=False, mode=mode)
        log_job(f"Pan ({direction})", job.id, prompt=prompt, mode=mode, source=job_id, index=index)
        if enqueue:
            return _enqueue_image_outputs(job, n=4)
        job = poll_with_progress(job, mode=mode)
        images = download_and_load_images(job)
        return io.NodeOutput(images[0:1], images[1:2], images[2:3], images[3:4], job.id,
                             ui=_preview_ui(images))


# ---------------------------------------------------------------------------
# 8. MidJourneyDownload — Job ID로 이미지 다운로드
# ---------------------------------------------------------------------------

class MidJourneyDownload(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MJ_Download",
            display_name="MidJourney Download",
            category="Midjourney",
            description="Job ID로 이미지를 다운로드합니다. 4장이면 4장, 1장(Upscale)이면 1장 출력.",
            inputs=[
                MJ_JOB_ID.Input("job_id", tooltip="다운로드할 Job ID"),
            ],
            outputs=[
                io.Image.Output(display_name="image_0"),
                io.Image.Output(display_name="image_1"),
                io.Image.Output(display_name="image_2"),
                io.Image.Output(display_name="image_3"),
            ],
        )

    @classmethod
    def execute(cls, job_id) -> io.NodeOutput:
        from midjourney_api.models import Job
        job = Job(id=job_id, prompt="")
        job.image_urls = [job.cdn_url(i) for i in range(4)]
        results = try_download_all(job)
        valid = [r for r in results if r is not None]
        preview = torch.cat(valid, dim=0) if valid else None
        outputs = [
            r if r is not None else ExecutionBlocker(None)
            for r in results
        ]
        return io.NodeOutput(*outputs,
                             ui=_preview_ui(preview) if preview is not None else None)


# ---------------------------------------------------------------------------
# 공통 헬퍼 — MJ_VIDEO_PARAMS + MJ_PARAMS 언팩
# ---------------------------------------------------------------------------

def _build_prompt(prompt: str, no: str) -> str:
    """prompt와 no를 조합합니다. no가 있으면 '--no <terms>' 접미사를 추가합니다."""
    p = (prompt or "").strip()
    n = (no or "").strip()
    if n:
        return f"{p} --no {n}".strip() if p else f"--no {n}"
    return p


def _video_kwargs(video_params) -> dict:
    """MJ_VIDEO_PARAMS에서 animate/extend_video 호환 kwargs를 추출합니다."""
    vp = dict(video_params) if video_params else {}
    return {
        "motion":     vp.get("motion"),
        "resolution": vp.get("resolution", VideoResolution.R480),
        "batch_size": vp.get("batch_size", 1),
        "mode":       vp.get("mode", SpeedMode.FAST),
        "stealth":    vp.get("stealth", False),
    }


# ---------------------------------------------------------------------------
# 9. MidJourneyAnimate — 이미지 → 비디오 생성
# ---------------------------------------------------------------------------

class MidJourneyAnimate(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MJ_Animate",
            display_name="MidJourney Animate",
            category="Midjourney",
            description="Midjourney 이미지를 비디오로 변환합니다.",
            inputs=[
                MJ_JOB_ID.Input("job_id", tooltip="원본 Imagine Job ID"),
                io.Int.Input("index", default=0, min=0, max=3,
                             tooltip="변환할 이미지 인덱스 (0-3)"),
                MJ_VIDEO_PARAMS.Input("video_params", optional=True),
                io.String.Input("prompt", default="", multiline=True,
                                tooltip="추가 프롬프트 (선택)"),
                io.String.Input("no", display_name="Negative", default="",
                                multiline=True, tooltip="네거티브 프롬프트 (--no)"),
            ],
            outputs=[
                MJ_JOB_ID.Output(display_name="job_id"),
            ],
        )

    @classmethod
    def execute(cls, job_id, index, video_params=None, prompt="", no="") -> io.NodeOutput:
        client = get_client()
        kw = _video_kwargs(video_params)
        job = client.animate(job_id, index, prompt=_build_prompt(prompt, no), wait=False, **kw)
        log_job("Animate", job.id, source=job_id, index=index, **kw)
        job = poll_with_progress(job, mode=kw["mode"])
        return io.NodeOutput(job.id)


# ---------------------------------------------------------------------------
# 10. MidJourneyAnimateFromImage — 이미지 파일 → 비디오 생성
# ---------------------------------------------------------------------------

class MidJourneyAnimateFromImage(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MJ_AnimateFromImage",
            display_name="MidJourney Animate From Image",
            category="Midjourney",
            description="이미지 텐서로 비디오를 생성합니다.",
            inputs=[
                io.Image.Input("start_image", tooltip="시작 프레임 이미지"),
                io.Image.Input("end_image", optional=True, tooltip="종료 프레임 이미지 (선택)"),
                io.Boolean.Input("loop", default=False,
                                 tooltip="루프 모드: end_image 대신 'loop' 전달 → 시작/끝 프레임이 이어지는 루프 비디오"),
                MJ_VIDEO_PARAMS.Input("video_params", optional=True),
                io.String.Input("prompt", default="", multiline=True,
                                tooltip="추가 프롬프트 (선택)"),
                io.String.Input("no", display_name="Negative", default="",
                                multiline=True, tooltip="네거티브 프롬프트 (--no)"),
            ],
            outputs=[
                MJ_JOB_ID.Output(display_name="job_id"),
            ],
        )

    @classmethod
    def execute(cls, start_image, end_image=None, loop=False, video_params=None,
                prompt="", no="") -> io.NodeOutput:
        client = get_client()
        start_path = image_tensor_to_temp_file(start_image)
        if loop:
            end_path = "loop"
        elif end_image is not None:
            end_path = image_tensor_to_temp_file(end_image)
        else:
            end_path = None
        kw = _video_kwargs(video_params)
        job = client.animate_from_image(start_path, end_path, prompt=_build_prompt(prompt, no),
                                        wait=False, **kw)
        log_job("AnimateFromImage", job.id, **kw)
        job = poll_with_progress(job, mode=kw["mode"])
        return io.NodeOutput(job.id)


# ---------------------------------------------------------------------------
# 11. MidJourneyExtendVideo — 비디오 연장
# ---------------------------------------------------------------------------

class MidJourneyExtendVideo(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MJ_ExtendVideo",
            display_name="MidJourney Extend Video",
            category="Midjourney",
            description="완료된 비디오 Job을 연장합니다.",
            inputs=[
                MJ_JOB_ID.Input("job_id", tooltip="비디오 Job ID"),
                io.Int.Input("index", default=0, min=0, max=3,
                             tooltip="연장할 배치 변형 인덱스"),
                io.Image.Input("end_image", optional=True, tooltip="종료 프레임 이미지 (선택)"),
                io.Boolean.Input("loop", default=False,
                                 tooltip="루프 모드: end_image 대신 'loop' 전달 → 시작/끝 프레임이 이어지는 루프 비디오"),
                MJ_VIDEO_PARAMS.Input("video_params", optional=True),
                io.String.Input("prompt", default="", multiline=True,
                                tooltip="추가 프롬프트 (선택)"),
                io.String.Input("no", display_name="Negative", default="",
                                multiline=True, tooltip="네거티브 프롬프트 (--no)"),
            ],
            outputs=[
                MJ_JOB_ID.Output(display_name="job_id"),
            ],
        )

    @classmethod
    def execute(cls, job_id, index, loop=False, video_params=None,
                end_image=None, prompt="", no="") -> io.NodeOutput:
        client = get_client()
        if loop:
            end_path = "loop"
        elif end_image is not None:
            end_path = image_tensor_to_temp_file(end_image)
        else:
            end_path = None
        kw = _video_kwargs(video_params)
        job = client.extend_video(job_id, index, end_image=end_path,
                                  prompt=_build_prompt(prompt, no), wait=False, **kw)
        log_job("ExtendVideo", job.id, source=job_id, index=index, **kw)
        job = poll_with_progress(job, mode=kw["mode"])
        return io.NodeOutput(job.id)


# ---------------------------------------------------------------------------
# 12. MidJourneyLoadVideo — 비디오를 메모리로 로드
# ---------------------------------------------------------------------------

class MidJourneyLoadVideo(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MJ_LoadVideo",
            display_name="MidJourney Load Video",
            category="Midjourney",
            description="비디오 Job ID로 비디오를 메모리에 로드합니다.",
            inputs=[
                MJ_JOB_ID.Input("job_id", tooltip="비디오 Job ID"),
                io.Int.Input("batch_index", default=0, min=0, max=3,
                             tooltip="다운로드할 배치 변형 인덱스"),
                io.Int.Input("size", optional=True,
                             tooltip="해상도 (예: 1080). 미지정 시 원본"),
            ],
            outputs=[
                io.Video.Output(display_name="video"),
            ],
        )

    @classmethod
    def execute(cls, job_id, batch_index=0, size=None) -> io.NodeOutput:
        from midjourney_api.models import Job
        client = get_client()
        job = Job(id=job_id, prompt="")
        data_list = client.download_video_bytes(job, size=size or None,
                                                batch_size=batch_index + 1)
        data = data_list[batch_index]
        log_job("LoadVideo", job_id, index=batch_index)
        return io.NodeOutput(video_bytes_to_video_input(data))
