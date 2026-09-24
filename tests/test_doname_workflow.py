import unittest
from unittest.mock import patch

from doname.domains import InputError
from doname.engine import check_domains
from doname.models import DomainResult, Evidence, Price
from doname.naming import screen_names
from doname.providers import ProviderResult


def report(domain, status, price=None, currency="EUR"):
    registration = Evidence("not_found", "RDAP")
    provider = Evidence("available" if status == "available_at_provider" else "unavailable", "SyntheticProvider")
    money = Price(str(price), currency, 1, "registration", "SyntheticProvider", provider.checked_at) if price is not None else None
    return DomainResult(domain, status, "synthetic", registration, provider, registration_price=money)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.rows = {
            "alpha.com": report("alpha.com", "available_at_provider", "12.00"),
            "alpha.fr": report("alpha.fr", "available_at_provider", "9.00"),
            "beta.com": report("beta.com", "unavailable_at_provider"),
            "beta.fr": report("beta.fr", "available_at_provider", "8.00"),
            "gamma.com": report("gamma.com", "available_at_provider"),
            "gamma.fr": report("gamma.fr", "available_at_provider", "7.00"),
        }
        self.patcher = patch("doname.naming.check_domains", side_effect=lambda domains, **_: [self.rows[d] for d in domains])
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_all_requires_both_extensions(self):
        result = screen_names(["alpha", "beta"], ["com", "fr"], match="all")
        self.assertEqual([x["name"] for x in result["candidates"]], ["alpha"])
        self.assertEqual(result["excluded"][0]["name"], "beta")

    def test_any_and_com_mandatory(self):
        any_result = screen_names(["alpha", "beta"], ["com", "fr"], match="any")
        self.assertEqual(len(any_result["candidates"]), 2)
        mandatory = screen_names(["alpha", "beta"], ["com", "fr"], match="any", required_extensions=["com"])
        self.assertEqual([x["name"] for x in mandatory["candidates"]], ["alpha"])

    def test_budget_unknown_price_is_not_free(self):
        result = screen_names(["alpha", "gamma"], ["com", "fr"], max_registration_price=15, currency="EUR")
        self.assertEqual([x["name"] for x in result["candidates"]], ["alpha"])
        self.assertEqual(result["excluded"][0]["match"], "unknown")
        self.assertIn("registration_price_unknown", result["excluded"][0]["reasons"][0])

    def test_available_only_hides_other_domains(self):
        result = screen_names(["alpha", "beta"], ["com", "fr"], available_only=True)
        self.assertEqual(result["excluded"], [])
        self.assertEqual(result["excluded_summary"]["excluded"], 1)

    def test_invalid_budget_and_required_extension(self):
        with self.assertRaises(InputError):
            screen_names(["alpha"], ["com"], max_registration_price=10)
        with self.assertRaises(InputError):
            screen_names(["alpha"], ["com"], required_extensions=["fr"])


class EngineTests(unittest.TestCase):
    def test_offline_mode_makes_no_network_calls(self):
        with patch("doname.engine.rdap.lookup") as rdap, patch("doname.engine.dns.observe") as dns:
            result = check_domains(["example.com"], offline=True, include_dns=True)
            rdap.assert_not_called()
            dns.assert_not_called()
        self.assertEqual(result[0].status, "not_verified")

    def test_partial_deadline_is_explicit(self):
        import time
        with patch("doname.engine._check_public", side_effect=lambda *args: (time.sleep(.2), (Evidence("registered", "RDAP"), None))[1]), patch("doname.engine.configured_provider", return_value=None):
            result = check_domains([f"name{i}.com" for i in range(10)], deadline_seconds=.02)
        self.assertEqual(len(result), 10)
        self.assertTrue(any(row.reason == "batch_deadline_exceeded" for row in result))


if __name__ == "__main__":
    unittest.main()
