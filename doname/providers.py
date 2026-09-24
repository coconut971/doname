"""Read-only provider protocol and GoDaddy v3 availability adapter."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol
from urllib.parse import urlencode

from .models import Evidence, Price
from .network import NetworkError, get_json, post_json


@dataclass
class ProviderResult:
    evidence: Evidence
    registration_price: Price | None = None
    renewal_price: Price | None = None


class AvailabilityProvider(Protocol):
    name: str

    def check_many(self, domains: list[str], timeout: float) -> dict[str, ProviderResult]: ...


def _price(raw: object, *, kind: str, years: int, checked_at: str) -> Price | None:
    if not isinstance(raw, dict):
        return None
    minor = raw.get("value")
    currency = raw.get("currencyCode")
    if type(minor) is not int or minor < 0 or not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha():
        return None
    return Price(str((Decimal(minor) / 100).quantize(Decimal("0.01"))), currency.upper(), years, kind, "GoDaddy", checked_at)


class GoDaddyProvider:
    name = "GoDaddy"
    endpoint = "https://api.godaddy.com/v3/domains/check-availability"

    def __init__(self, token: str):
        if not token or "\n" in token or "\r" in token:
            raise ValueError("Invalid provider token")
        self._token = token

    def check(self, domain: str, timeout: float = 3.0) -> ProviderResult:
        # The endpoint is fixed. Only the validated ASCII domain enters the query.
        url = f"{self.endpoint}?{urlencode({'domain': domain, 'optimizeFor': 'ACCURACY'})}"
        try:
            data = get_json(url, headers={"Authorization": f"Bearer {self._token}"}, timeout=timeout)
        except NetworkError as exc:
            status = "rate_limited" if exc.code == "http_429" else "timeout" if exc.code == "timeout" else "error"
            return ProviderResult(Evidence(status, self.name, reason=exc.code, retry_after_seconds=exc.retry_after_seconds))
        return self._parse_item(domain, data)

    def check_many(self, domains: list[str], timeout: float = 4.0) -> dict[str, ProviderResult]:
        if not 1 <= len(domains) <= 25 or len(set(domains)) != len(domains):
            raise ValueError("GoDaddy accepts 1 to 25 distinct domains")
        try:
            data = post_json(self.endpoint, {"domains": domains, "optimizeFor": "ACCURACY"},
                             headers={"Authorization": f"Bearer {self._token}"}, timeout=timeout)
        except NetworkError as exc:
            status = "rate_limited" if exc.code == "http_429" else "timeout" if exc.code == "timeout" else "error"
            return {domain: ProviderResult(Evidence(status, self.name, reason=exc.code,
                                                   retry_after_seconds=exc.retry_after_seconds)) for domain in domains}
        items = data.get("items")
        if not isinstance(items, list) or len(items) != len(domains):
            return {domain: ProviderResult(Evidence("error", self.name, reason="invalid_batch_payload")) for domain in domains}
        return {domain: self._parse_item(domain, item) for domain, item in zip(domains, items)}

    def _parse_item(self, domain: str, data: object) -> ProviderResult:
        if not isinstance(data, dict) or str(data.get("domain", "")).lower() != domain:
            return ProviderResult(Evidence("error", self.name, reason="invalid_availability_payload"))
        if isinstance(data.get("error"), dict):
            code = data["error"].get("name")
            if code in {"UNSUPPORTED_TLD", "TLD_NOT_SUPPORTED"}:
                return ProviderResult(Evidence("unsupported", self.name, reason="provider_tld_not_supported"))
            return ProviderResult(Evidence("error", self.name, reason="provider_item_error"))
        if type(data.get("available")) is not bool:
            return ProviderResult(Evidence("error", self.name, reason="invalid_availability_payload"))
        if "definitive" in data and type(data["definitive"]) is not bool:
            return ProviderResult(Evidence("error", self.name, reason="invalid_availability_payload"))
        available = data["available"]
        evidence = Evidence("available" if available else "unavailable", self.name,
                            reason=None if available else "provider_did_not_offer_registration",
                            details={"definitive": data.get("definitive"), "optimization": "ACCURACY"})
        if not available:
            return ProviderResult(evidence)
        prices = data.get("prices")
        if prices is not None and not isinstance(prices, list):
            evidence.reason = "pricing_payload_invalid"
            return ProviderResult(evidence)
        terms = [term for term in prices or [] if isinstance(term, dict) and term.get("term") == "YEAR" and type(term.get("period")) is int and 1 <= term["period"] <= 10]
        terms.sort(key=lambda term: term["period"])
        for term in terms:
            registration = _price(term.get("price"), kind="registration", years=term["period"], checked_at=evidence.checked_at)
            if registration:
                renewal = _price(term.get("renewalPrice"), kind="renewal", years=term["period"], checked_at=evidence.checked_at)
                return ProviderResult(evidence, registration, renewal)
        evidence.reason = "pricing_not_provided_or_invalid"
        return ProviderResult(evidence)
