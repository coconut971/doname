"""Run the public, credential-free release checks without GitHub Actions."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", action="append", dest="pythons", metavar="VERSION",
                        help="Python version for tests; repeat to check more than one")
    args = parser.parse_args()

    for executable in ("uv", "node"):
        if shutil.which(executable) is None:
            parser.error(f"{executable} is required for the local release check")

    project_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    project_version = re.search(r'^version = "([^"]+)"$', project_text, re.MULTILINE)
    if project_version is None:
        raise SystemExit("Missing package version in pyproject.toml")
    plugin = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    package_text = (ROOT / "doname" / "__init__.py").read_text(encoding="utf-8")
    package_version = re.search(r'^__version__ = "([^"]+)"$', package_text, re.MULTILINE)
    if package_version is None:
        raise SystemExit("Missing package version in doname/__init__.py")
    versions = {project_version.group(1), plugin["version"], package_version.group(1)}
    if len(versions) != 1:
        raise SystemExit("Package, plugin and server versions disagree")
    print(f"DoName version {package_version.group(1)}: local release check", flush=True)

    environment = os.environ.copy()
    for key in ("GODADDY_PAT", "CONTROL_PLANE_API_KEY"):
        environment.pop(key, None)
    environment["UV_NO_PROGRESS"] = "1"

    commands = [
        ["uv", "lock", "--check"],
        ["uv", "sync", "--locked", "--dev"],
    ]
    for version in dict.fromkeys(args.pythons or [None]):
        commands.append(["uv", "run", "--locked", *(["--python", version] if version else []),
                         "python", "-m", "unittest", "discover", "-s", "tests", "-q"])
    commands += [
        ["uv", "run", "--locked", "python", "scripts/validate_manifests.py"],
        ["node", "scripts/ui_smoke.js"],
        ["uv", "run", "--locked", "python", "scripts/build_plugin.py"],
        ["uv", "run", "--locked", "python", "scripts/smoke_bundle.py"],
        ["uv", "build", "--quiet"],
        ["uv", "run", "--locked", "python", "scripts/audit_artifacts.py"],
    ]
    for command in commands:
        print("+", " ".join(command), flush=True)
        result = subprocess.run(command, cwd=ROOT, env=environment, check=False)
        if result.returncode:
            raise SystemExit(result.returncode)
    print("Local release checks passed; no live provider request was made.", flush=True)


if __name__ == "__main__":
    main()
