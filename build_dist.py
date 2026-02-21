#!/usr/bin/env python3
"""배포용 빌드 스크립트 — Cython .py -> .so/.pyd 컴파일 + JS 미니파이 + dist/ 패키징.

사전 준비:
    pip install cython setuptools

사용법:
    python build_dist.py                # 기본 빌드
    python build_dist.py --minify-js    # JS 미니파이 포함 (npm i -g terser 필요)
    python build_dist.py --no-cleanup   # 빌드 중간 파일 유지 (디버깅용)

결과물:
    dist/ComfyUI-MidjourneyAPI/         # 이 폴더를 custom_nodes/에 복사
"""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DIST_DIR = ROOT / "dist"
PKG_NAME = "ComfyUI-MidjourneyAPI"

# ---------------------------------------------------------------------------
# Cython 컴파일 대상 (.py -> .so/.pyd)
# ---------------------------------------------------------------------------
COMPILE_TARGETS = [
    "utils.py",
    "nodes/const.py",
    "nodes/generation.py",
    "nodes/params.py",
    "nodes/style.py",
    "nodes/keywords.py",
    "nodes/keyword_join.py",
    "nodes/keyword_random.py",
]

# 패키지 진입점 — 소스 그대로 복사 (import 글루 코드만 포함)
KEEP_PY = [
    "__init__.py",
    "nodes/__init__.py",
]

# 데이터 디렉토리 (통째로 복사)
DATA_DIRS = ["mj", "web", "presets"]

# 메타 파일
META_FILES = ["pyproject.toml", "requirements.txt"]


# ---------------------------------------------------------------------------
# 1단계: Cython 컴파일
# ---------------------------------------------------------------------------

def _generate_setup_py() -> str:
    """Cython 컴파일용 임시 setup.py 내용 생성."""
    ext_lines = []
    for t in COMPILE_TARGETS:
        module_name = t.replace("/", ".").removesuffix(".py")
        ext_lines.append(f'    Extension("{module_name}", ["{t}"]),')

    return f"""\
import sys
sys.path.insert(0, {str(ROOT)!r})
from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
{chr(10).join(ext_lines)}
]

setup(
    ext_modules=cythonize(
        extensions,
        compiler_directives={{"language_level": "3"}},
        build_dir="build/cython_temp",
    ),
)
"""


def step_compile(out: Path):
    """Cython으로 .py -> .so/.pyd 컴파일 후 dist/에 수집."""
    print("\n[1/4] Cython compile")

    setup_py = ROOT / "_setup_cython.py"
    setup_py.write_text(_generate_setup_py(), encoding="utf-8")

    try:
        subprocess.check_call(
            [sys.executable, str(setup_py), "build_ext", "--inplace"],
            cwd=str(ROOT),
        )
    finally:
        setup_py.unlink(missing_ok=True)

    # 컴파일된 .so/.pyd 파일을 dist/로 수집
    so_ext = ".pyd" if platform.system() == "Windows" else ".so"
    collected = 0

    for target in COMPILE_TARGETS:
        stem = Path(target).stem
        parent = Path(target).parent
        search_dir = ROOT / parent if str(parent) != "." else ROOT

        found = sorted(search_dir.glob(f"{stem}*{so_ext}"))
        if not found:
            print(f"  [WARN] not found: {target}")
            continue

        so_file = found[0]
        dest_dir = out / parent if str(parent) != "." else out
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(so_file, dest_dir / so_file.name)
        collected += 1
        print(f"  [OK] {so_file.name}")

    print(f"  => {collected}/{len(COMPILE_TARGETS)} modules compiled")


# ---------------------------------------------------------------------------
# 2단계: __init__.py 복사
# ---------------------------------------------------------------------------

def step_copy_init(out: Path):
    """패키지 진입점 __init__.py 파일 복사."""
    print("\n[2/4] Copy __init__.py")
    for f in KEEP_PY:
        src = ROOT / f
        dest = out / f
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        print(f"  [OK] {f}")


# ---------------------------------------------------------------------------
# 3단계: 데이터 + 메타 파일 복사 (+ 선택적 JS 미니파이)
# ---------------------------------------------------------------------------

def step_copy_data(out: Path, minify_js: bool):
    """데이터 디렉토리, 메타 파일 복사. --minify-js 시 JS 미니파이."""
    print("\n[3/4] Copy data & meta")

    for d in DATA_DIRS:
        src = ROOT / d
        if src.is_dir():
            shutil.copytree(src, out / d, dirs_exist_ok=True)
            print(f"  [OK] {d}/")

    for f in META_FILES:
        src = ROOT / f
        if src.exists():
            shutil.copy2(src, out / f)
            print(f"  [OK] {f}")

    if minify_js:
        _minify_js_files(out / "web")


def _minify_js_files(web_dir: Path):
    """terser로 web/ 내 JS 파일 미니파이."""
    if not shutil.which("terser"):
        print("  [WARN] terser not installed, skipping JS minification")
        print("         Install: npm install -g terser")
        return

    for js_file in sorted(web_dir.glob("*.js")):
        result = subprocess.run(
            ["terser", str(js_file), "--compress", "--mangle", "-o", str(js_file)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"  [OK] minified {js_file.name}")
        else:
            print(f"  [WARN] terser failed for {js_file.name}: {result.stderr.strip()}")


# ---------------------------------------------------------------------------
# 4단계: 빌드 아티팩트 정리
# ---------------------------------------------------------------------------

def step_cleanup():
    """소스 트리의 빌드 중간 파일 정리."""
    print("\n[4/4] Cleanup")

    so_ext = ".pyd" if platform.system() == "Windows" else ".so"

    # 소스 트리에 생성된 .so/.pyd 삭제
    for target in COMPILE_TARGETS:
        stem = Path(target).stem
        parent = Path(target).parent
        search_dir = ROOT / parent if str(parent) != "." else ROOT
        for f in search_dir.glob(f"{stem}*{so_ext}"):
            f.unlink()
            print(f"  [OK] removed {f.relative_to(ROOT)}")

    # Cython이 생성한 .c 파일 삭제
    for target in COMPILE_TARGETS:
        c_file = ROOT / target.replace(".py", ".c")
        if c_file.exists():
            c_file.unlink()
            print(f"  [OK] removed {c_file.relative_to(ROOT)}")

    # build/ 디렉토리 삭제
    build_dir = ROOT / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print("  [OK] removed build/")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Cython build: .py -> .so/.pyd + dist packaging",
    )
    parser.add_argument("--minify-js", action="store_true", help="Minify JS with terser")
    parser.add_argument("--no-cleanup", action="store_true", help="Keep intermediate build files")
    args = parser.parse_args()

    out = DIST_DIR / PKG_NAME
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    step_compile(out)
    step_copy_init(out)
    step_copy_data(out, minify_js=args.minify_js)

    if not args.no_cleanup:
        step_cleanup()

    # 결과 요약
    so_ext = ".pyd" if platform.system() == "Windows" else ".so"
    so_count = len(list(out.rglob(f"*{so_ext}")))
    print(f"\n{'=' * 55}")
    print(f"Build complete: {out}")
    print(f"Compiled modules: {so_count} ({so_ext})")
    print(f"")
    print(f"Deploy:")
    print(f"  cp -r {out} <ComfyUI>/custom_nodes/")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
