"""Read-only provider protocol and GoDaddy v3 availability adapter."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from collections import deque
import threading
import time
from typing import Protocol
from urllib.parse import urlencode

from .models import Evidence, Price
from .network import NetworkError, get_json, post_json

# GoDaddy Money.value is in the currency's smallest unit, not always cents.
# Unknown currencies deliberately produce no displayed price.
_MINOR_DIGITS = {
    **dict.fromkeys(("CLP", "ISK", "JPY", "KRW", "VND", "XAF", "XOF", "XPF"), 0),
    **dict.fromkeys(("AED", "ARS", "AUD", "BGN", "BRL", "CAD", "CHF", "CNY", "CZK", "DKK",
                     "EUR", "GBP", "HKD", "HUF", "ILS", "INR", "MXN", "MYR", "NOK", "NZD",
                     "PHP", "PLN", "RON", "SAR", "SEK", "SGD", "THB", "TRY", "TWD", "USD", "ZAR"), 2),
    **dict.fromkeys(("BHD", "IQD", "JOD", "KWD", "LYD", "OMR", "TND"), 3),
}


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
    if type(minor) is not int or minor < 0 or not isinstance(currency, str):
        return None
    currency = currency.upper()
    digits = _MINOR_DIGITS.get(currency)
    if digits is None:
        return None
    scale = Decimal(10) ** digits
    amount = (Decimal(minor) / scale).quantize(Decimal(1) / scale)
    return Price(str(amount), currency, years, kind, "GoDaddy", checked_at)


class GoDaddyProvider:
    name = "GoDaddy"
    endpoint = "https://api.godaddy.com/v3/domains/check-availability"

    def __init__(self, token: str):
        if not token or "\n" in token or "\r" in token:
            raise ValueError("Invalid provider token")
        self._token = token
        self._calls: deque[float] = deque()
        self._cooldown_until = 0.0
        self._lock = threading.Lock()

    def _admit(self) -> ProviderResult | None:
        with self._lock:
            current = time.monotonic()
            while self._calls and current - self._calls[0] >= 60:
                self._calls.popleft()
            delay = self._cooldown_until - current
            if len(self._calls) >= 55:
                delay = max(delay, 60 - (current - self._calls[0]))
            if delay > 0:
                return ProviderResult(Evidence("rate_limited", self.name, reason="local_or_provider_cooldown",
                                               retry_after_seconds=max(1, int(delay + .999))))
            self._calls.append(current)
        return None

    def _on_network_error(self, exc: NetworkError) -> ProviderResult:
        if exc.code == "http_429":
            with self._lock:
                self._cooldown_until = max(self._cooldown_until, time.monotonic() + (exc.retry_after_seconds or 60))
        status = "rate_limited" if exc.code == "http_429" else "timeout" if exc.code == "timeout" else "error"
        return ProviderResult(Evidence(status, self.name, reason=exc.code, retry_after_seconds=exc.retry_after_seconds))

    def check(self, domain: str, timeout: float = 3.0) -> ProviderResult:
        # The endpoint is fixed. Only the validated ASCII domain enters the query.
        url = f"{self.endpoint}?{urlencode({'domain': domain, 'optimizeFor': 'ACCURACY'})}"
        limited = self._admit()
        if limited:
            return limited
        try:
            data = get_json(url, headers={"Authorization": f"Bearer {self._token}"}, timeout=timeout)
        except NetworkError as exc:
            return self._on_network_error(exc)
        return self._parse_item(domain, data)

    def check_many(self, domains: list[str], timeout: float = 4.0) -> dict[str, ProviderResult]:
        if not 1 <= len(domains) <= 25 or len(set(domains)) != len(domains):
            raise ValueError("GoDaddy accepts 1 to 25 distinct domains")
        limited = self._admit()
        if limited:
            return {domain: limited for domain in domains}
        try:
            data = post_json(self.endpoint, {"domains": domains, "optimizeFor": "ACCURACY"},
                             headers={"Authorization": f"Bearer {self._token}"}, timeout=timeout)
        except NetworkError as exc:
            return {domain: self._on_network_error(exc) for domain in domains}
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
        if available and data.get("definitive") is not True:
            return ProviderResult(Evidence("unconfirmed", self.name,
                                           reason="provider_availability_not_definitive",
                                           details={"reported_available": True,
                                                    "definitive": data.get("definitive"),
                                                    "optimization": "ACCURACY"}))
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
