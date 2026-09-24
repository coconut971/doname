"""Portable MCP server: stdio locally, Streamable HTTP on loopback."""

from __future__ import annotations

import argparse
from importlib.resources import files
from typing import Annotated, Any

from mcp.server import MCPServer
from mcp.types import CallToolResult, TextContent, ToolAnnotations
from pydantic import BaseModel

from . import __version__
from .engine import check_domains as engine_check, configured_provider
from .naming import screen_names as engine_screen

UI_URI = "ui://doname/cards/v2.html"
READ_EXTERNAL = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True)
READ_LOCAL = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)


class CapabilitiesOutput(BaseModel):
    name: str
    version: str
    provider: str | None
    keyless: bool
    purchasing: bool
    telemetry: bool
    limits: "LimitsOutput"
    note: str


class LimitsOutput(BaseModel):
    names: int
    extensions: int
    domains: int


class EvidenceOutput(BaseModel):
    status: str
    source: str
    checked_at: str
    reason: str | None
    retry_after_seconds: int | None
    details: dict[str, Any]
    age_seconds: int


class PriceOutput(BaseModel):
    amount: str
    currency: str
    period_years: int
    kind: str
    provider: str
    checked_at: str
    indicative: bool


class DomainOutput(BaseModel):
    domain: str
    status: str
    reason: str
    registration: EvidenceOutput | None
    registrability: EvidenceOutput | None
    dns: EvidenceOutput | None
    registration_price: PriceOutput | None
    renewal_price: PriceOutput | None


class CheckOutput(BaseModel):
    summary: str
    checked: int
    domains: list[DomainOutput]


class ConstraintsOutput(BaseModel):
    extensions: list[str]
    match: str
    required_extensions: list[str]
    max_registration_price: str | None
    currency: str | None
    available_only: bool


class CandidateOutput(BaseModel):
    name: str
    match: str
    domains: list[DomainOutput]
    reasons: list[str]


class ExcludedSummaryOutput(BaseModel):
    excluded: int
    unverified: int


class ScreenOutput(BaseModel):
    summary: str
    constraints: ConstraintsOutput
    checked_domains: int
    candidates: list[CandidateOutput]
    excluded: list[CandidateOutput]
    excluded_summary: ExcludedSummaryOutput
    note: str


def _domain_line(item: dict[str, Any]) -> str:
    parts = [f"{item['domain']}: {item['status']} ({item['reason']})"]
    for label, key in (("RDAP", "registration"), ("provider", "registrability"), ("DNS", "dns")):
        evidence = item.get(key)
        if evidence:
            reason = f", {evidence['reason']}" if evidence.get("reason") else ""
            parts.append(f"{label} {evidence['status']} via {evidence['source']} at {evidence['checked_at']} "
                         f"({evidence['age_seconds']}s old{reason})")
    for label, key in (("register", "registration_price"), ("renew", "renewal_price")):
        price = item.get(key)
        if price:
            parts.append(f"{label} {price['amount']} {price['currency']} / {price['period_years']} year(s) "
                         f"via {price['provider']} at {price['checked_at']} (indicative)")
    return "; ".join(parts)


mcp = MCPServer(
    "DoName", version=__version__,
    instructions="The host AI invents and judges names. Use screen_names once for a bounded batch and explicit TLD/budget constraints; use check_domains for exact domains. Only available_at_provider means a registrar offered registration at check time. RDAP 404 and DNS NXDOMAIN do not confirm availability. No trademark clearance or purchasing.",
)


@mcp.tool(title="DoName capabilities", annotations=READ_LOCAL)
def capabilities() -> Annotated[CallToolResult, CapabilitiesOutput]:
    """Check DoName's provider configuration, keyless mode and batch limits without sending a domain or exposing credentials."""
    data = {"name": "DoName", "version": __version__, "provider": "GoDaddy" if configured_provider() else None,
            "keyless": True, "purchasing": False, "telemetry": False,
            "limits": {"names": 12, "extensions": 5, "domains": 25},
            "note": "Without provider credentials, RDAP can confirm registration or report no object; it cannot confirm purchase availability."}
    provider_text = data["provider"] or "none (keyless RDAP)"
    return CallToolResult(content=[TextContent(type="text", text=f"DoName {__version__}; provider: {provider_text}; 25 domains per batch. No purchasing or telemetry. {data['note']}")], structured_content=data)


@mcp.tool(title="Check exact domains", annotations=READ_EXTERNAL)
def check_domains(domains: list[str], include_dns: bool = False, offline: bool = False) -> Annotated[CallToolResult, CheckOutput]:
    """Check 1–25 exact registrable domains in one bounded batch. Returns separate RDAP registration, provider registrability/prices and optional DNS observations with source and time. No brief is sent to providers. offline disables all network checks."""
    reports = engine_check(domains, include_dns=include_dns, offline=offline)
    counts: dict[str, int] = {}
    for report in reports:
        counts[report.status] = counts.get(report.status, 0) + 1
    summary = ", ".join(f"{count} {status}" for status, count in sorted(counts.items()))
    data = {"summary": summary, "checked": len(reports), "domains": [report.to_dict() for report in reports]}
    lines = [f"Checked {len(reports)} domains: {summary}."]
    lines.extend(_domain_line(item) for item in data["domains"])
    lines.append("Prices are indicative; provider renewal rates may differ from manual renewal rates.")
    return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))], structured_content=data)


@mcp.tool(title="Screen project names", annotations=READ_EXTERNAL,
          meta={"ui": {"resourceUri": UI_URI}})
def screen_names(names: list[str], extensions: list[str] | None = None, match: str = "all",
                 required_extensions: list[str] | None = None, max_registration_price: float | None = None,
                 currency: str | None = None, available_only: bool = False, offline: bool = False) -> Annotated[CallToolResult, ScreenOutput]:
    """Screen up to 12 AI-generated base names across 1–5 public suffixes (max 25 domains). match='all' requires every extension; 'any' requires one. required_extensions enforces mandatory TLDs such as .com. Budget applies to each domain's total first registration term in its stated currency; unknown prices never pass. available_only shows only verified available domains in eligible names. Returns grouped evidence and concise reasons. No brief or purchase action."""
    data = engine_screen(names, extensions, match=match, required_extensions=required_extensions,
                         max_registration_price=max_registration_price, currency=currency,
                         available_only=available_only, offline=offline)
    lines = [data["summary"]]
    for item in data["candidates"] + data["excluded"]:
        lines.append(f"{item['name']}: {item['match']}")
        for domain in item["domains"]:
            lines.append("  " + _domain_line(domain))
        if item["reasons"]:
            lines.append("  Exclusions: " + "; ".join(item["reasons"]))
    if available_only:
        lines.append("Other names hidden by available_only; counts remain in excluded_summary.")
    lines.append("Provider offers and indicative prices can change. Provider renewal rates may differ from manual renewal rates. Domain research is not trademark clearance.")
    return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))], structured_content=data)


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
