"""Build a source-based portable Agent Plugin bundle without local/private state."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
# Keep this list explicit: a local file under doname/ or skills/ must never
# enter a public bundle merely because it happens to be next to source code.
FILES = [
    "LICENSE", "README.md", "mcp.json", "plugin.json", "pyproject.toml", "uv.lock",
    "doname/__init__.py", "doname/cli.py", "doname/dns.py", "doname/domains.py",
    "doname/engine.py", "doname/mcp_server.py", "doname/models.py", "doname/naming.py",
    "doname/network.py", "doname/providers.py", "doname/rdap.py", "doname/ui/cards.html",
    "skills/doname-naming/SKILL.md",
]


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
