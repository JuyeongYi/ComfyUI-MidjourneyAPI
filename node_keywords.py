"""keywords/ 폴더의 서브폴더/파일 계층으로부터 키워드 그룹 노드를 동적으로 생성.

구조: mj/keywords/<subfolder>/<category>.txt
  → ComfyUI 카테고리: Midjourney/keywords/<Subfolder>
  → node_id: MJ_KW_<Subfolder><Category>
"""
from pathlib import Path
from comfy_api.latest import io
import folder_paths

_PLUGIN_KEYWORDS_DIR = Path(__file__).parent / "mj" / "keywords"
_COMFY_ROOT = Path(folder_paths.base_path)
_USER_KEYWORDS_DIR = _COMFY_ROOT / "user" / "mj" / "keywords"


def _load_keywords(path: Path) -> list[str]:
    """한 줄에 하나씩 키워드 로드. #으로 시작하는 줄은 무시."""
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def _collect_keyword_files() -> dict[tuple[str, str], list[Path]]:
    """두 경로를 재귀 스캔. (subfolder, stem) → [Path, ...] 반환.

    - 서브폴더 안의 파일: subfolder = 첫 번째 폴더명
    - 루트 직속 파일: subfolder = ""
    - 동일 키에 해당하는 파일은 모두 수집 (user가 plugin 키워드에 추가됨)
    """
    files: dict[tuple[str, str], list[Path]] = {}
    for base_dir in (_PLUGIN_KEYWORDS_DIR, _USER_KEYWORDS_DIR):
        if not base_dir.is_dir():
            continue
        for p in sorted(base_dir.rglob("*.txt")):
            rel_parts = p.relative_to(base_dir).parts
            subfolder = rel_parts[0] if len(rel_parts) > 1 else ""
            key = (subfolder, p.stem)
            files.setdefault(key, []).append(p)
    return files


def _merge_keywords(paths: list[Path]) -> list[str]:
    """여러 파일의 키워드를 순서 유지하며 중복 없이 병합."""
    seen: set[str] = set()
    merged: list[str] = []
    for path in paths:
        for kw in _load_keywords(path):
            if kw not in seen:
                seen.add(kw)
                merged.append(kw)
    return merged


def _make_keyword_node(node_id: str, display_name: str, category: str, keywords: list[str]):
    """type() + 클로저로 Combo → String 노드 클래스 동적 생성."""

    def _define_schema(cls):
        return io.Schema(
            node_id=node_id,
            display_name=display_name,
            category=category,
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
    """두 경로를 재귀 스캔해 노드 목록 반환."""
    nodes = []
    for (subfolder, stem), paths in sorted(_collect_keyword_files().items()):
        keywords = _merge_keywords(paths)
        if not keywords:
            continue
        display_name = stem.replace("_", " ").title()
        if subfolder:
            subfolder_title = subfolder.replace("_", " ").title()
            node_id = f"MJ_KW_{subfolder_title.replace(' ', '')}_{display_name.replace(' ', '')}"
            category = f"Midjourney/keywords/{subfolder_title}"
        else:
            node_id = f"MJ_KW_{display_name.replace(' ', '')}"
            category = "Midjourney/keywords"
        nodes.append(_make_keyword_node(node_id, display_name, category, keywords))
    return nodes


KEYWORD_NODES = load_keyword_nodes()
