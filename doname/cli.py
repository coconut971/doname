"""Diagnostic CLI over the same engine exposed by MCP."""

from __future__ import annotations

import argparse
import json

from .domains import InputError
from .engine import check_domains, configured_provider
from .naming import screen_names


def main() -> None:
    parser = argparse.ArgumentParser(prog="doname", description="DoName domain research diagnostics")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("capabilities")
    check = commands.add_parser("check")
    check.add_argument("domains", nargs="+")
    check.add_argument("--offline", action="store_true")
    check.add_argument("--dns", action="store_true")
    screen = commands.add_parser("screen")
    screen.add_argument("names", nargs="+")
    screen.add_argument("--extensions", nargs="+", default=["com", "fr"])
    screen.add_argument("--match", choices=["all", "any"], default="all")
    screen.add_argument("--required", nargs="+")
    screen.add_argument("--budget", type=float)
    screen.add_argument("--currency")
    screen.add_argument("--available-only", action="store_true")
    screen.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "capabilities":
            output = {"name": "DoName", "provider": "GoDaddy" if configured_provider() else None,
                      "keyless": True, "purchasing": False, "telemetry": False,
                      "limits": {"names": 12, "extensions": 5, "domains": 25}}
        elif args.command == "check":
            results = check_domains(args.domains, include_dns=args.dns, offline=args.offline)
            output = {"checked": len(results), "domains": [item.to_dict() for item in results]}
        else:
            output = screen_names(args.names, args.extensions, match=args.match, required_extensions=args.required,
                                  max_registration_price=args.budget, currency=args.currency,
                                  available_only=args.available_only, offline=args.offline)
    except (InputError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
