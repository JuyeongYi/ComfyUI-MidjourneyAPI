"""keywords/ 폴더의 .txt 파일로부터 키워드 그룹 노드를 동적으로 생성."""
from pathlib import Path
from comfy_api.latest import io
import folder_paths

_PLUGIN_KEYWORDS_DIR = Path(__file__).parent / "keywords"
_COMFY_ROOT = Path(folder_paths.base_path)
_USER_KEYWORDS_DIR = _COMFY_ROOT / "user" / "mj_keywords"


def _load_keywords(path: Path) -> list[str]:
    """한 줄에 하나씩 키워드 로드. #으로 시작하는 줄은 무시."""
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def _collect_keyword_files() -> dict[str, Path]:
    """두 경로를 스캔. 동일 stem은 user 경로가 우선. stem → Path 반환."""
    files: dict[str, Path] = {}
    if _PLUGIN_KEYWORDS_DIR.is_dir():
        for p in sorted(_PLUGIN_KEYWORDS_DIR.glob("*.txt")):
            files[p.stem] = p
    if _USER_KEYWORDS_DIR.is_dir():
        for p in sorted(_USER_KEYWORDS_DIR.glob("*.txt")):
            files[p.stem] = p
    return files


def _make_keyword_node(node_id: str, display_name: str, keywords: list[str]):
    """type() + 클로저로 Combo → String 노드 클래스 동적 생성."""

    def _define_schema(cls):
        return io.Schema(
            node_id=node_id,
            display_name=display_name,
            category="Midjourney/keywords",
            inputs=[
                io.Combo.Input("keyword", options=keywords, default=keywords[0]),
            ],
            outputs=[
                io.String.Output(display_name="keyword"),
            ],
        )

    def _execute(cls, keyword) -> io.NodeOutput:
        return io.NodeOutput(keyword)

    return type(node_id, (io.ComfyNode,), {
        "define_schema": classmethod(_define_schema),
        "execute": classmethod(_execute),
    })


def load_keyword_nodes() -> list[type[io.ComfyNode]]:
    """두 경로를 스캔해 노드 목록 반환. 사용자 파일 우선."""
    nodes = []
    for stem, path in sorted(_collect_keyword_files().items()):
        keywords = _load_keywords(path)
        if not keywords:
            continue
        display_name = stem.replace("_", " ").title()
        node_id = "MJ_KW_" + display_name.replace(" ", "")
        nodes.append(_make_keyword_node(node_id, display_name, keywords))
    return nodes


KEYWORD_NODES = load_keyword_nodes()
