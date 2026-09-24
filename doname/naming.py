"""Group checked domains by name and apply explicit AND/OR constraints."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal, InvalidOperation

from .domains import InputError, candidate_batch, tlds
from .engine import check_domains
from .models import DomainResult
from .providers import AvailabilityProvider


def _price_limit(value: float | None, currency: str | None) -> tuple[Decimal | None, str | None]:
    if value is None:
        if currency is not None:
            raise InputError("A currency is only used with a registration budget.")
        return None, None
    try:
        limit = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise InputError("Invalid registration budget.") from None
    if not limit.is_finite() or limit < 0 or limit > 1_000_000:
        raise InputError("Registration budget must be between 0 and 1,000,000.")
    if not isinstance(currency, str) or len(currency.strip()) != 3 or not currency.strip().isalpha():
        raise InputError("A three-letter currency is required with a budget.")
    return limit, currency.strip().upper()


def _domain_outcome(report: DomainResult, budget: Decimal | None, currency: str | None) -> tuple[str, str]:
    if report.status == "available_at_provider":
        if budget is None:
            return "pass", "available_at_provider"
        price = report.registration_price
        if price is None:
            return "unknown", "registration_price_unknown"
        if price.currency != currency:
            return "unknown", "currency_mismatch"
        if Decimal(price.amount) > budget:
            return "fail", "over_budget"
        return "pass", "available_within_budget"
    if report.status in {"registered", "unavailable_at_provider"}:
        return "fail", report.status
    return "unknown", report.status


def _aggregate(outcomes: list[str], mode: str) -> str:
    if mode == "all":
        return "fail" if "fail" in outcomes else "unknown" if "unknown" in outcomes else "pass"
    return "pass" if "pass" in outcomes else "unknown" if "unknown" in outcomes else "fail"


def screen_names(names: list[str], extensions: list[str] | None = None, *, match: str = "all",
                 required_extensions: list[str] | None = None, max_registration_price: float | None = None,
                 currency: str | None = None, available_only: bool = False, offline: bool = False,
                 provider: AvailabilityProvider | None = None) -> dict:
    if match not in {"all", "any"}:
        raise InputError("match must be 'all' or 'any'.")
    suffixes = tlds(extensions)
    required = tlds(required_extensions) if required_extensions is not None else []
    if any(suffix not in suffixes for suffix in required):
        raise InputError("Required extensions must also appear in extensions.")
    budget, requested_currency = _price_limit(max_registration_price, currency)
    batches = candidate_batch(names, suffixes)
    domains = [domain for _, group in batches for domain in group]
    reports = {item.domain: item for item in check_domains(domains, provider=provider, offline=offline)}
    candidates = []
    excluded = []
    counts: Counter[str] = Counter()
    for name, group in batches:
        evaluations = {domain: _domain_outcome(reports[domain], budget, requested_currency) for domain in group}
        required_domains = [f"{name}.{suffix}" for suffix in required]
        required_outcome = _aggregate([evaluations[domain][0] for domain in required_domains], "all") if required_domains else "pass"
        overall = _aggregate([evaluations[domain][0] for domain in group], match)
        decision = _aggregate([required_outcome, overall], "all")
        counts[decision] += 1
        item = {
            "name": name,
            "match": decision,
            "domains": [reports[domain].to_dict() for domain in group],
            "reasons": [f"{domain}: {evaluations[domain][1]}" for domain in group if evaluations[domain][0] != "pass"],
        }
        if decision == "pass":
            candidates.append(item)
        elif not available_only:
            excluded.append(item)
    return {
        "summary": f"{counts['pass']} eligible, {counts['fail']} excluded, {counts['unknown']} unverified candidate names.",
        "constraints": {"extensions": suffixes, "match": match, "required_extensions": required,
                        "max_registration_price": str(budget) if budget is not None else None, "currency": requested_currency,
                        "available_only": available_only},
        "checked_domains": len(domains),
        "candidates": candidates,
        "excluded": excluded,
        "excluded_summary": {"excluded": counts["fail"], "unverified": counts["unknown"]},
        "note": "Provider availability and prices are scoped to that provider and check time; domain research is not trademark clearance.",
    }
