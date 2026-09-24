"""Optional DNS observation. Its output never means purchasable or registered."""

from __future__ import annotations

import dns.exception
import dns.resolver

from .models import Evidence


def observe(domain: str, timeout: float = 2.0) -> Evidence:
    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = timeout
    try:
        answer = resolver.resolve(domain, "NS")
    except dns.resolver.NXDOMAIN:
        return Evidence("nxdomain", "system DNS resolver", reason="name_not_found_in_dns")
    except dns.resolver.NoAnswer:
        return Evidence("no_ns_answer", "system DNS resolver")
    except dns.exception.Timeout:
        return Evidence("timeout", "system DNS resolver")
    except (dns.exception.DNSException, OSError):
        return Evidence("error", "system DNS resolver")
    return Evidence("records_found" if answer else "no_ns_answer", "system DNS resolver")
