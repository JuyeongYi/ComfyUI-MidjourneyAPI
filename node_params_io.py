"""SaveImagineParams / LoadImagineParams — 프리셋 저장·로드 노드."""

from __future__ import annotations

from comfy_api.latest import io

from .node_imagine_v7_params import MJ_PARAMS
from .utils import list_presets, load_preset, save_preset


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
