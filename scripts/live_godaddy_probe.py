"""Manual GoDaddy v3 contract probe. Never run in public CI or save its output."""

from __future__ import annotations

import json
import os
import secrets

from doname.engine import check_domains
from doname.models import DomainResult, Evidence, Price
from doname.providers import GoDaddyProvider


def _evidence(value: Evidence | None) -> dict | None:
    if value is None:
        return None
    return {
        "status": value.status,
        "source": value.source,
        "checked_at": value.checked_at,
        "reason": value.reason,
        "retry_after_seconds": value.retry_after_seconds,
        "definitive": value.details.get("definitive"),
    }


def _price(value: Price | None) -> dict | None:
    if value is None:
        return None
    return {
        "amount": value.amount,
        "currency": value.currency,
        "period_years": value.period_years,
        "provider": value.provider,
        "checked_at": value.checked_at,
        "indicative": value.indicative,
    }


def summarize(case: str, extension: str, result: DomainResult) -> dict:
    # Deliberately do not include the queried domain, raw response or token.
    return {
        "case": case,
        "extension": extension,
        "status": result.status,
        "reason": result.reason,
        "rdap": _evidence(result.registration),
        "provider": _evidence(result.registrability),
        "registration_price": _price(result.registration_price),
        "renewal_price": _price(result.renewal_price),
    }


def main() -> None:
    token = os.environ.get("GODADDY_PAT")
    if not token:
        raise SystemExit("GODADDY_PAT is absent; no live provider checks were made.")

    # Publicly known registered names plus high-entropy, non-user candidates.
    random_label = f"doname-probe-{secrets.token_hex(8)}"
    cases = [
        ("registered_com", "com", "example.com"),
        ("registered_fr", "fr", "nic.fr"),
        ("candidate_com", "com", f"{random_label}.com"),
        ("candidate_fr", "fr", f"{random_label}.fr"),
    ]
    try:
        rows = check_domains([domain for _, _, domain in cases], provider=GoDaddyProvider(token))
    except Exception as exc:
        # Unexpected errors can contain request context. Only print the class.
        raise SystemExit(f"Probe failed: {type(exc).__name__}") from None

    by_domain = {row.domain: row for row in rows}
    for case, extension, domain in cases:
        print(json.dumps(summarize(case, extension, by_domain[domain]), separators=(",", ":")))

    registered_ok = all(by_domain[domain].registration is not None and
                        by_domain[domain].registration.status == "registered"
                        for _, _, domain in cases[:2])
    candidates_ok = all(by_domain[domain].status == "available_at_provider" and
                        by_domain[domain].registration_price is not None
                        for _, _, domain in cases[2:])
    print(json.dumps({"live_criteria_met": registered_ok and candidates_ok,
                      "registered_evidence": registered_ok,
                      "available_and_priced_com_fr": candidates_ok,
                      "renewal_is_optional": True}, separators=(",", ":")))
    if not registered_ok or not candidates_ok:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
