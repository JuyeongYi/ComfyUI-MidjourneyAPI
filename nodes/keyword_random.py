"""랜덤 키워드 노드 — 카테고리(파일)에서 키워드 1개를 랜덤 선택."""

import random

from comfy_api.latest import io

from .keywords import _collect_keyword_files, _merge_keywords


def _build_category_map() -> dict[str, list]:
    """(subfolder, stem) → "subfolder/stem" 문자열 키로 변환한 카테고리 맵 반환."""
    raw = _collect_keyword_files()
    return {
        f"{subfolder}/{stem}" if subfolder else stem: paths
        for (subfolder, stem), paths in sorted(raw.items())
    }


_CATEGORY_MAP = _build_category_map()
_CATEGORY_OPTIONS = list(_CATEGORY_MAP.keys())


class MidJourneyKeywordRandom(io.ComfyNode):

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="MJ_KeywordRandom",
            display_name="Keyword Random",
            category="Midjourney/keywords",
            inputs=[
                io.Combo.Input(
                    "category",
                    options=_CATEGORY_OPTIONS,
                    default=_CATEGORY_OPTIONS[0] if _CATEGORY_OPTIONS else "",
                    tooltip="키워드를 선택할 카테고리 (subcategory/filename)",
                ),
                io.Int.Input(
                    "seed",
                    default=0,
                    min=0,
                    max=2**32 - 1,
                    control_after_generate=True,
                    tooltip="랜덤 시드 — 같은 시드는 항상 같은 키워드를 반환",
                ),
            ],
            outputs=[
                io.String.Output(display_name="keyword"),
            ],
        )

    @classmethod
    def execute(cls, category: str, seed: int) -> io.NodeOutput:
        paths = _CATEGORY_MAP.get(category, [])
        if not paths:
            return io.NodeOutput("")
        keywords = _merge_keywords(paths)
        if not keywords:
            return io.NodeOutput("")
        rng = random.Random(seed)
        return io.NodeOutput(rng.choice(keywords))
