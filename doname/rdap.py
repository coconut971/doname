"""Keyless registration evidence from IANA-discovered RDAP services."""

from __future__ import annotations

import ipaddress
import threading
import time
from urllib.parse import quote, urlsplit

from .models import Evidence
from .network import NetworkError, get_json

BOOTSTRAP_URL = "https://data.iana.org/rdap/dns.json"
_CACHE: tuple[float, dict[str, str]] | None = None
_LOCK = threading.Lock()
_TTL = 86400
_COOLDOWNS: dict[str, float] = {}
_COOLDOWN_LOCK = threading.Lock()


def _safe_base(url: str) -> bool:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host or parsed.username or parsed.password or parsed.query or parsed.fragment:
        return False
    if host == "localhost" or host.endswith((".local", ".internal", ".test")):
        return False
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return True
    return False


def _bootstrap(timeout: float) -> dict[str, str]:
    global _CACHE
    if _CACHE and time.monotonic() - _CACHE[0] < _TTL:
        return _CACHE[1]
    with _LOCK:
        if _CACHE and time.monotonic() - _CACHE[0] < _TTL:
            return _CACHE[1]
        data = get_json(BOOTSTRAP_URL, timeout=timeout, max_bytes=2_000_000)
        services = data.get("services")
        if not isinstance(services, list):
            raise NetworkError("invalid_bootstrap")
        mapping = {}
        for item in services:
            if not isinstance(item, list) or len(item) != 2 or not isinstance(item[0], list) or not isinstance(item[1], list):
                continue
            bases = [base.rstrip("/") for base in item[1] if isinstance(base, str) and _safe_base(base)]
            if bases:
                for suffix in item[0]:
                    if isinstance(suffix, str) and suffix.isascii():
                        mapping[suffix.lower()] = bases[0]
        if not mapping:
            raise NetworkError("invalid_bootstrap")
        _CACHE = (time.monotonic(), mapping)
        return mapping


def lookup(domain: str, timeout: float = 3.0) -> Evidence:
    try:
        mapping = _bootstrap(timeout)
    except NetworkError as exc:
        status = "rate_limited" if exc.code == "http_429" else "timeout" if exc.code == "timeout" else "error"
        return Evidence(status, "IANA RDAP bootstrap", reason=exc.code,
                        retry_after_seconds=exc.retry_after_seconds)
    tld = domain.rsplit(".", 1)[-1]
    base = mapping.get(tld)
    if not base:
        return Evidence("unsupported", "IANA RDAP bootstrap", reason="tld_not_listed")
    source = urlsplit(base).hostname or "RDAP"
    with _COOLDOWN_LOCK:
        delay = _COOLDOWNS.get(source, 0) - time.monotonic()
    if delay > 0:
        return Evidence("rate_limited", source, reason="rdap_retry_after",
                        retry_after_seconds=max(1, int(delay + .999)))
    try:
        data = get_json(f"{base}/domain/{quote(domain, safe='')}", timeout=timeout)
    except NetworkError as exc:
        if exc.code == "http_404":
            return Evidence("not_found", source, reason="rdap_object_not_found")
        if exc.code == "http_429":
            with _COOLDOWN_LOCK:
                _COOLDOWNS[source] = max(_COOLDOWNS.get(source, 0), time.monotonic() + (exc.retry_after_seconds or 60))
        status = "rate_limited" if exc.code == "http_429" else "timeout" if exc.code == "timeout" else "error"
        return Evidence(status, source, reason=exc.code, retry_after_seconds=exc.retry_after_seconds)
    if data.get("objectClassName") != "domain" or str(data.get("ldhName", "")).lower().rstrip(".") != domain:
        return Evidence("error", source, reason="invalid_domain_object")
    details = {}
    for event in data.get("events", []) if isinstance(data.get("events"), list) else []:
        if isinstance(event, dict) and event.get("eventAction") in {"registration", "expiration"} and isinstance(event.get("eventDate"), str):
            details[event["eventAction"]] = event["eventDate"][:64]
    return Evidence("registered", source, details=details)
