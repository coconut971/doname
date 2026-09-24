"""Reject unexpected files in release artifacts before publishing them."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import zipfile

from build_plugin import FILES, ROOT


def _safe_name(name: str) -> None:
    path = PurePosixPath(name)
    parts = path.parts
    if path.is_absolute() or ".." in parts or "\\" in name:
        raise SystemExit(f"Unsafe archive path: {name}")
    if any(part.lower() in {".env", ".secrets", "secrets", "__pycache__", ".git"}
           or part.lower().startswith(".env.") for part in parts):
        raise SystemExit(f"Private path in artifact: {name}")
    if path.suffix.lower() in {".key", ".pem", ".p12", ".pfx", ".log"}:
        raise SystemExit(f"Private file type in artifact: {name}")


def main() -> None:
    dist = ROOT / "dist"
    with zipfile.ZipFile(dist / "doname-plugin.zip") as archive:
        names = archive.namelist()
        if len(names) != len(FILES) or set(names) != set(FILES):
            raise SystemExit("Plugin bundle differs from its explicit public file list")
        for name in names:
            _safe_name(name)

    wheels = list(dist.glob("doname-*.whl"))
    sdists = list(dist.glob("doname-*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise SystemExit("Expected exactly one DoName wheel and sdist")
    with zipfile.ZipFile(wheels[0]) as archive:
        for name in archive.namelist():
            _safe_name(name)
            if not (name.startswith("doname/") or ".dist-info/" in name):
                raise SystemExit(f"Unexpected wheel file: {name}")

    tracked = None
    if (ROOT / ".git").exists():
        output = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
        tracked = {path.decode("utf-8") for path in output.split(b"\0") if path}
    with tarfile.open(sdists[0], "r:gz") as archive:
        for member in archive.getmembers():
            _safe_name(member.name)
            if not (member.isfile() or member.isdir()):
                raise SystemExit(f"Unexpected sdist member type: {member.name}")
            if not member.isfile() or tracked is None:
                continue
            parts = PurePosixPath(member.name).parts[1:]
            relative = PurePosixPath(*parts).as_posix()
            generated = (relative in {"PKG-INFO", "setup.cfg"}
                         or relative.startswith("doname.egg-info/"))
            if not generated and relative not in tracked:
                raise SystemExit(f"Untracked file in sdist: {relative}")
    print("Release artifacts contain only expected public files")


if __name__ == "__main__":
    main()
