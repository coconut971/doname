"""Synthetic, network-free reproducible engine measurement."""

from __future__ import annotations

import json
import time
from unittest.mock import patch

from doname.models import Evidence, Price
from doname.naming import screen_names
from doname.providers import ProviderResult


class SyntheticProvider:
    name = "SyntheticProvider"

    def __init__(self):
        self.calls = 0

    def check_many(self, domains, timeout):
        self.calls += 1
        results = {}
        for domain in domains:
            evidence = Evidence("available", self.name)
            price = Price("12.00", "EUR", 1, "registration", self.name, evidence.checked_at)
            results[domain] = ProviderResult(evidence, price)
        return results


def main() -> None:
    provider = SyntheticProvider()
    names = [f"testname{i}" for i in range(12)]
    calls = 0

    def rdap_lookup(domain, timeout):
        nonlocal calls
        calls += 1
        return Evidence("not_found", "Synthetic RDAP")

    with patch("doname.engine.rdap.lookup", side_effect=rdap_lookup):
        start = time.perf_counter()
        result = screen_names(names, ["com", "fr"], provider=provider)
        elapsed = (time.perf_counter() - start) * 1000
    print(json.dumps({"synthetic_names": len(names), "domains": result["checked_domains"],
                      "eligible": len(result["candidates"]), "rdap_calls": calls,
                      "provider_batch_calls": provider.calls,
                      "local_elapsed_ms": round(elapsed, 2),
                      "json_bytes": len(json.dumps(result, separators=(",", ":")).encode("utf-8"))}))


if __name__ == "__main__":
    main()
