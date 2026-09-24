"""Build a source-based portable Agent Plugin bundle without local/private state."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
FILES = ["plugin.json", "mcp.json", "uv.lock", "pyproject.toml", "README.md", "LICENSE"]
FILES += [path.relative_to(ROOT).as_posix() for folder in ("doname", "skills/doname-naming")
          for path in (ROOT / folder).rglob("*") if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"]


def main() -> None:
    target = ROOT / "dist" / "doname-plugin.zip"
    target.parent.mkdir(exist_ok=True)
    with ZipFile(target, "w", compression=ZIP_DEFLATED) as archive:
        for name in sorted(set(FILES)):
            source = ROOT / name
            if not source.is_file():
                raise FileNotFoundError(source)
            info = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, source.read_bytes())
    print(f"Built {target} with {len(set(FILES))} public source/config files")


if __name__ == "__main__":
    main()
