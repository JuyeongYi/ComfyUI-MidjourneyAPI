"""ComfyUI-MidJourney node definitions (V3 schema)."""

from __future__ import annotations

import torch
from comfy_api.latest import io, ui
from comfy_execution.graph import ExecutionBlocker

from .node_imagine_v7_params import ImagineV7Params, MJ_PARAMS  # noqa: F401
from .node_params_io import LoadImagineParams, SaveImagineParams  # noqa: F401
from .utils import (
    download_and_load_images,
    get_client,
    log_job,
    poll_with_progress,
    try_download_all,
)


def _preview_ui(images: torch.Tensor) -> ui.PreviewImage:
    return ui.PreviewImage(images)


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
            ],
            outputs=[
                io.Image.Output(display_name="image_0"),
                io.Image.Output(display_name="image_1"),
                io.Image.Output(display_name="image_2"),
                io.Image.Output(display_name="image_3"),
                io.String.Output(display_name="job_id"),
            ],
        )

    @classmethod
    def execute(cls, prompt, no, params=None) -> io.NodeOutput:
        client = get_client()

        kwargs = dict(params) if params else {}
        mode = kwargs.pop("mode", "fast")

        if no:
            kwargs["no"] = no

        job = client.imagine(prompt, wait=False, mode=mode, **kwargs)
        log_job("Imagine", job.id, prompt=prompt, mode=mode, **kwargs)
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
                io.String.Input("job_id", tooltip="원본 Job ID"),
                io.Int.Input("index", default=0, min=0, max=3,
                             tooltip="변형할 이미지 인덱스 (0-3)"),
                io.Boolean.Input("strong", default=True,
                                 tooltip="True=Strong, False=Subtle"),
                io.Combo.Input("mode", options=["fast", "relax", "turbo"], default="fast"),
            ],
            outputs=[
                io.Image.Output(display_name="image_0"),
                io.Image.Output(display_name="image_1"),
                io.Image.Output(display_name="image_2"),
                io.Image.Output(display_name="image_3"),
                io.String.Output(display_name="job_id"),
            ],
        )

    @classmethod
    def execute(cls, job_id, index, strong, mode) -> io.NodeOutput:
        client = get_client()
        label = "Strong" if strong else "Subtle"
        job = client.vary(job_id, index, strong=strong, wait=False, mode=mode)
        log_job(f"Vary ({label})", job.id, mode=mode, source=job_id, index=index)
        job = poll_with_progress(job, mode=mode)
        images = download_and_load_images(job)
        return io.NodeOutput(images[0:1], images[1:2], images[2:3], images[3:4], job.id,
                             ui=_preview_ui(images))


# ---------------------------------------------------------------------------
# 6. MidJourneyUpscale — 확대
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
                io.String.Input("job_id", tooltip="원본 Job ID"),
                io.Int.Input("index", default=0, min=0, max=3,
                             tooltip="확대할 이미지 인덱스 (0-3)"),
                io.Combo.Input("upscale_type",
                               options=["v7_2x_subtle", "v7_2x_creative"],
                               default="v7_2x_subtle"),
                io.Combo.Input("mode", options=["fast", "relax", "turbo"], default="fast"),
            ],
            outputs=[
                io.Image.Output(display_name="image"),
                io.String.Output(display_name="job_id"),
            ],
        )

    @classmethod
    def execute(cls, job_id, index, upscale_type, mode) -> io.NodeOutput:
        client = get_client()
        job = client.upscale(job_id, index, upscale_type=upscale_type, wait=False, mode=mode)
        log_job("Upscale", job.id, mode=mode, source=job_id, index=index, type=upscale_type)
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
                io.String.Input("job_id", tooltip="원본 Job ID"),
                io.Int.Input("index", default=0, min=0, max=3,
                             tooltip="확장할 이미지 인덱스 (0-3)"),
                io.Combo.Input("direction",
                               options=["up", "down", "left", "right"],
                               default="up"),
                io.String.Input("prompt", default="", multiline=True, optional=True,
                                tooltip="추가 프롬프트 (선택)"),
                io.Combo.Input("mode", options=["fast", "relax", "turbo"], default="fast"),
            ],
            outputs=[
                io.Image.Output(display_name="image_0"),
                io.Image.Output(display_name="image_1"),
                io.Image.Output(display_name="image_2"),
                io.Image.Output(display_name="image_3"),
                io.String.Output(display_name="job_id"),
            ],
        )

    @classmethod
    def execute(cls, job_id, index, direction, mode, prompt="") -> io.NodeOutput:
        client = get_client()
        job = client.pan(job_id, index, direction=direction, prompt=prompt or "", wait=False, mode=mode)
        log_job(f"Pan ({direction})", job.id, prompt=prompt, mode=mode, source=job_id, index=index)
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
                io.String.Input("job_id", tooltip="다운로드할 Job ID"),
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


