"""기존 mj/style/ 루트의 스타일 파일을 mj/style/7/ 로 이동.

사용법:
    python migrate_styles_to_v7.py [--dry-run]

옵션:
    --dry-run  실제 이동 없이 이동할 파일 목록만 출력
"""
import shutil
import sys
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

def migrate(base_dir: Path, dry_run: bool = False):
    v7_dir = base_dir / "7"
    moved = 0
    skipped = 0

    for p in sorted(base_dir.iterdir()):
        # 정수 이름 폴더(버전 폴더)는 건너뜀
        if p.is_dir():
            try:
                int(p.name)
                continue
            except ValueError:
                print(f"  [skip] 알 수 없는 폴더: {p.name}")
                continue

        if p.suffix.lower() not in IMAGE_EXTS or "__" not in p.stem:
            print(f"  [skip] 규칙 불일치: {p.name}")
            skipped += 1
            continue

        dest = v7_dir / p.name
        print(f"  {'(dry)' if dry_run else ''} {p.name}  →  7/{p.name}")
        if not dry_run:
            v7_dir.mkdir(exist_ok=True)
            shutil.move(str(p), str(dest))
        moved += 1

    print(f"\n총 {moved}개 이동{'(예정)' if dry_run else ''}, {skipped}개 건너뜀.")


def main():
    dry_run = "--dry-run" in sys.argv
    script_dir = Path(__file__).parent
    targets = [
        script_dir / "mj" / "style",
    ]

    # ComfyUI 루트의 user 스타일 디렉터리도 처리 (존재하는 경우)
    comfy_root = script_dir.parent.parent
    user_style = comfy_root / "user" / "mj" / "style"
    if user_style.is_dir():
        targets.append(user_style)

    for target in targets:
        if not target.is_dir():
            print(f"[없음] {target}")
            continue
        print(f"\n[{target}]")
        migrate(target, dry_run=dry_run)


if __name__ == "__main__":
    main()
