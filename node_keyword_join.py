"""MidJourney KeywordJoin node — Autogrow 가변 입력으로 키워드 연결."""
from comfy_api.latest import io


class MidJourneyKeywordJoin(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MJ_KeywordJoin",
            display_name="Keyword Join",
            category="Midjourney/keywords",
            description="여러 키워드 문자열을 하나로 합칩니다.",
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
                io.Combo.Input("separator", options=[", ", " ", " | ", " + "], default=", "),
            ],
            outputs=[
                io.String.Output(display_name="keywords"),
            ],
        )

    @classmethod
    def execute(cls, keywords: io.Autogrow.Type, separator=", ") -> io.NodeOutput:
        parts = [v.strip() for v in keywords.values() if v and v.strip()]
        return io.NodeOutput(separator.join(parts))
