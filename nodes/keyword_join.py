"""MidJourney KeywordJoin node — Autogrow 가변 입력으로 키워드 연결."""
from comfy_api.latest import io


class MidJourneyKeywordJoin(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MJ_KeywordJoin",
            display_name="Keyword Join",
            category="Midjourney/keywords",
            description="유저 프롬프트와 여러 키워드를 하나로 합칩니다.",
            inputs=[
                io.Autogrow.Input(
                    "keywords",
                    template=io.Autogrow.TemplatePrefix(
                        io.String.Input("keyword", default=""),
                        prefix="keyword",
                        min=1,
                        max=100,
                    ),
                ),
                io.String.Input("base", display_name="Base Keywords", default="",
                                multiline=True, optional=True,
                                tooltip="유저 프롬프트 — 그대로 첫 번째 항목으로 추가됩니다."),
                io.Combo.Input("prompt_position", display_name="Prompt on",
                               options=["First", "Last"], default="First"),
                io.Combo.Input("separator", options=[", ", " ", " | ", " + "], default=", "),
            ],
            outputs=[
                io.String.Output(display_name="keywords"),
            ],
        )

    @classmethod
    def execute(cls, keywords: io.Autogrow.Type, base="", prompt_position="First", separator=", ") -> io.NodeOutput:
        kw_parts = [v.strip() for v in keywords.values() if v and v.strip()]
        base_part = [base.strip()] if base and base.strip() else []
        parts = base_part + kw_parts if prompt_position == "First" else kw_parts + base_part
        return io.NodeOutput(separator.join(parts))
