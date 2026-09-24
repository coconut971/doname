"""Validate public plugin manifests against local Agent Plugins 1.0.0 schemas."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas" / "agent-plugins-1.0.0"
SCHEMAS = {
    "plugin.json": (
        "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "0a4aad95ce337878ad38802ebf0daa3fde76abe3f65400c86bcbb1ec0b3ab883",
    ),
    "mcp.json": (
        "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
        "6539175bfcdf43085855183e86da40ea94b166547a72b47ae9a0a390516d3acb",
    ),
}


def main() -> None:
    for name, (url, expected_hash) in SCHEMAS.items():
        raw = (SCHEMA_ROOT / f"{name.removesuffix('.json')}.schema.json").read_bytes()
        if len(raw) > 65_536 or hashlib.sha256(raw).hexdigest() != expected_hash:
            raise ValueError(f"Unexpected Agent Plugins 1.0.0 schema content for {name}")
        schema = json.loads(raw)
        if schema.get("$id") != url:
            raise ValueError(f"Incorrect schema identifier for {name}")
        Draft202012Validator.check_schema(schema)
        document = json.loads((ROOT / name).read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(document)
        print(f"{name}: Agent Plugins 1.0.0 schema valid")


if __name__ == "__main__":
    main()
