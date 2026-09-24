"""Bounded evidence collection and honest status resolution."""

from __future__ import annotations

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait

from . import dns, rdap
from .domains import exact_batch
from .models import DomainResult, Evidence
from .providers import AvailabilityProvider, GoDaddyProvider, ProviderResult

MAX_WORKERS = 4
CALL_TIMEOUT = 3.0
TOTAL_DEADLINE = 18.0
_PROVIDER: GoDaddyProvider | None = None
_PROVIDER_TOKEN: str | None = None
_PROVIDER_LOCK = threading.Lock()


def configured_provider() -> AvailabilityProvider | None:
    global _PROVIDER, _PROVIDER_TOKEN
    token = os.environ.get("GODADDY_PAT")
    if not token:
        with _PROVIDER_LOCK:
            _PROVIDER = None
            _PROVIDER_TOKEN = None
        return None
    with _PROVIDER_LOCK:
        if _PROVIDER is None or token != _PROVIDER_TOKEN:
            _PROVIDER = GoDaddyProvider(token)
            _PROVIDER_TOKEN = token
        return _PROVIDER


def resolve(domain: str, registration: Evidence | None, provider: ProviderResult | None, dns_evidence: Evidence | None = None) -> DomainResult:
    registry = registration.status if registration else "not_checked"
    offer = provider.evidence.status if provider else "not_configured"
    if registry == "registered" and offer == "available":
        status, reason = "conflict", "rdap_registered_but_provider_available"
    elif registry == "registered":
        status, reason = "registered", "rdap_domain_object"
    elif offer == "available":
        status, reason = "available_at_provider", "provider_reports_available"
    elif offer == "unavailable":
        status, reason = "unavailable_at_provider", "provider_did_not_offer_registration"
    elif registry == "not_found":
        status, reason = "not_found_in_registration_data", "rdap_404_is_not_availability"
    else:
        status, reason = "not_verified", (provider.evidence.reason if provider and provider.evidence.reason else registration.reason if registration and registration.reason else "no_registration_or_provider_confirmation")
    return DomainResult(domain, status, reason, registration, provider.evidence if provider else None, dns_evidence,
                        provider.registration_price if provider and status == "available_at_provider" else None,
                        provider.renewal_price if provider and status == "available_at_provider" else None)


def _check_public(domain: str, include_dns: bool, deadline: float) -> tuple[Evidence | None, Evidence | None]:
    registration = None
    dns_evidence = None
    remaining = deadline - time.monotonic()
    if remaining > 0:
        registration = rdap.lookup(domain, min(CALL_TIMEOUT, remaining))
    if include_dns and deadline - time.monotonic() > 0:
        dns_evidence = dns.observe(domain, min(2.0, deadline - time.monotonic()))
    return registration, dns_evidence


def check_domains(domains: list[str], *, provider: AvailabilityProvider | None = None,
                  include_dns: bool = False, offline: bool = False, deadline_seconds: float = TOTAL_DEADLINE) -> list[DomainResult]:
    checked = exact_batch(domains)
    if not 0 < deadline_seconds <= 30:
        raise ValueError("deadline_seconds must be between 0 and 30")
    if provider is None and not offline:
        provider = configured_provider()
    if offline:
        return [DomainResult(domain, "not_verified", "offline_mode_no_live_checks") for domain in checked]
    deadline = time.monotonic() + deadline_seconds
    pool = ThreadPoolExecutor(max_workers=MAX_WORKERS + 1, thread_name_prefix="doname-check")
    try:
        provider_future = pool.submit(provider.check_many, checked, min(4.0, deadline_seconds)) if provider else None
        futures = {pool.submit(_check_public, domain, include_dns, deadline): domain for domain in checked}
        all_futures = list(futures) + ([provider_future] if provider_future else [])
        done, pending = wait(all_futures, timeout=deadline_seconds)
        public = {}
        for future in done:
            if future is provider_future:
                continue
            domain = futures[future]
            try:
                public[domain] = future.result()
            except Exception:
                public[domain] = (Evidence("error", "RDAP", reason="check_failed"), None)
        for future in pending:
            future.cancel()
            if future is provider_future:
                continue
            domain = futures[future]
            public[domain] = (Evidence("timeout", "RDAP", reason="batch_deadline_exceeded"), None)
        offers = {}
        if provider_future:
            if provider_future in done:
                try:
                    offers = provider_future.result()
                except Exception:
                    offers = {}
            else:
                offers = {domain: ProviderResult(Evidence("timeout", provider.name, reason="batch_deadline_exceeded")) for domain in checked}
        results = []
        for domain in checked:
            registration, dns_evidence = public[domain]
            offer = offers.get(domain)
            if provider and offer is None:
                offer = ProviderResult(Evidence("error", provider.name, reason="missing_provider_result"))
            results.append(resolve(domain, registration, offer, dns_evidence))
        return results
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
