"""Extract the distributable plugin and run its stdio MCP command in isolation."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import shutil
import tempfile
from zipfile import ZipFile

from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "dist" / "doname-plugin.zip"
EXPECTED_TOOLS = {"capabilities", "check_domains", "screen_names"}


async def smoke(plugin_root: Path) -> None:
    config = json.loads((plugin_root / "mcp.json").read_text(encoding="utf-8"))
    server = config["mcpServers"]["doname"]
    if server["type"] != "stdio":
        raise AssertionError("The bundle must start a local stdio MCP server")
    command = shutil.which(server["command"])
    if command is None:
        raise RuntimeError(f"Missing executable: {server['command']}")
    args = [arg.replace("${PLUGIN_ROOT}", str(plugin_root)) for arg in server["args"]]
    cwd = server["cwd"].replace("${PLUGIN_ROOT}", str(plugin_root))
    environment = os.environ.copy()
    for key in ("GODADDY_PAT", "PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "UV_PROJECT", "UV_PROJECT_ENVIRONMENT"):
        environment.pop(key, None)
    environment.update(UV_LINK_MODE="copy", UV_NO_PROGRESS="1")
    params = StdioServerParameters(command=command, args=args, cwd=cwd, env=environment)
    async with Client(params, read_timeout_seconds=90) as client:
        listed = await client.list_tools()
        names = {tool.name for tool in listed.tools}
        if names != EXPECTED_TOOLS:
            raise AssertionError(f"Unexpected MCP tools: {sorted(names)}")
        screen_tool = next(tool for tool in listed.tools if tool.name == "screen_names")
        ui_uri = screen_tool.meta["ui"]["resourceUri"]
        capabilities = await client.call_tool("capabilities", {})
        if capabilities.is_error or capabilities.structured_content.get("provider") is not None:
            raise AssertionError("Extracted bundle failed keyless capabilities")
        screened = await client.call_tool("screen_names", {
            "names": ["donameci"], "extensions": ["com", "fr"], "offline": True,
        })
        if screened.is_error or screened.structured_content.get("checked_domains") != 2:
            raise AssertionError("Extracted bundle failed offline naming")
        ui = await client.read_resource(ui_uri)
        if "ui/resource-teardown" not in ui.contents[0].text:
            raise AssertionError("Extracted UI resource is missing teardown support")
    print("Extracted bundle: stdio MCP startup, tool discovery, calls and UI resource OK")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="doname-bundle-") as temporary:
        plugin_root = Path(temporary).resolve()
        with ZipFile(BUNDLE) as archive:
            for item in archive.infolist():
                destination = (plugin_root / item.filename).resolve()
                if destination != plugin_root and plugin_root not in destination.parents:
                    raise ValueError("Plugin bundle contains a path outside its root")
            archive.extractall(plugin_root)
        asyncio.run(asyncio.wait_for(smoke(plugin_root), timeout=120))


if __name__ == "__main__":
    main()
