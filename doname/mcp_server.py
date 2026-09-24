"""Portable MCP server: stdio locally, Streamable HTTP on loopback."""

from __future__ import annotations

import argparse
from importlib.resources import files
from typing import Any, TypedDict

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from . import __version__
from .engine import check_domains as engine_check, configured_provider
from .naming import screen_names as engine_screen

UI_URI = "ui://doname/cards/v1.html"
READ_EXTERNAL = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True)
READ_LOCAL = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)


class CapabilitiesOutput(TypedDict):
    name: str
    version: str
    provider: str | None
    keyless: bool
    purchasing: bool
    telemetry: bool
    limits: dict[str, int]
    note: str


class CheckOutput(TypedDict):
    summary: str
    checked: int
    domains: list[dict[str, Any]]


class ScreenOutput(TypedDict):
    summary: str
    constraints: dict[str, Any]
    checked_domains: int
    candidates: list[dict[str, Any]]
    excluded: list[dict[str, Any]]
    excluded_summary: dict[str, int]
    note: str


mcp = MCPServer(
    "DoName", version=__version__,
    instructions="The host AI invents and judges names. Use screen_names once for a bounded batch and explicit TLD/budget constraints; use check_domains for exact domains. Only available_at_provider means a registrar offered registration at check time. RDAP 404 and DNS NXDOMAIN do not confirm availability. No trademark clearance or purchasing.",
)


@mcp.tool(title="DoName capabilities", annotations=READ_LOCAL, structured_output=True)
def capabilities() -> CapabilitiesOutput:
    """Check DoName's provider configuration, keyless mode and batch limits without sending a domain or exposing credentials."""
    return {"name": "DoName", "version": __version__, "provider": "GoDaddy" if configured_provider() else None,
            "keyless": True, "purchasing": False, "telemetry": False,
            "limits": {"names": 12, "extensions": 5, "domains": 25},
            "note": "Without provider credentials, RDAP can confirm registration or report no object; it cannot confirm purchase availability."}


@mcp.tool(title="Check exact domains", annotations=READ_EXTERNAL, structured_output=True)
def check_domains(domains: list[str], include_dns: bool = False, offline: bool = False) -> CheckOutput:
    """Check 1–25 exact registrable domains in one bounded batch. Returns separate RDAP registration, provider registrability/prices and optional DNS observations with source and time. No brief is sent to providers. offline disables all network checks."""
    reports = engine_check(domains, include_dns=include_dns, offline=offline)
    counts: dict[str, int] = {}
    for report in reports:
        counts[report.status] = counts.get(report.status, 0) + 1
    summary = ", ".join(f"{count} {status}" for status, count in sorted(counts.items()))
    return {"summary": summary, "checked": len(reports), "domains": [report.to_dict() for report in reports]}


@mcp.tool(title="Screen project names", annotations=READ_EXTERNAL,
          meta={"ui": {"resourceUri": UI_URI}}, structured_output=True)
def screen_names(names: list[str], extensions: list[str] | None = None, match: str = "all",
                 required_extensions: list[str] | None = None, max_registration_price: float | None = None,
                 currency: str | None = None, available_only: bool = False, offline: bool = False) -> ScreenOutput:
    """Screen up to 12 AI-generated base names across 1–5 public suffixes (max 25 domains). match='all' requires every extension; 'any' requires one. required_extensions enforces mandatory TLDs such as .com. Budget is the total first registration term in its stated currency; unknown prices never pass. available_only hides nonmatching names. Returns grouped evidence and concise reasons. No brief or purchase action."""
    return engine_screen(names, extensions, match=match, required_extensions=required_extensions,
                         max_registration_price=max_registration_price, currency=currency,
                         available_only=available_only, offline=offline)


@mcp.resource(UI_URI, name="doname_cards", title="DoName domain cards",
              mime_type="text/html;profile=mcp-app")
def domain_cards() -> str:
    """Compact, local-only visualisation of DoName screen results."""
    return files("doname").joinpath("ui/cards.html").read_text(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(prog="doname-mcp")
    parser.add_argument("--http", action="store_true", help="Run Streamable HTTP on 127.0.0.1/mcp instead of stdio")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.http:
        if not 1 <= args.port <= 65535:
            parser.error("port must be between 1 and 65535")
        mcp.run(transport="streamable-http", host="127.0.0.1", port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
