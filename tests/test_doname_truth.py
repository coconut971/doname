import unittest
from unittest.mock import patch

from doname.domains import InputError, candidate_batch, exact_batch, exact_domain, tlds
from doname.engine import resolve
from doname.models import Evidence
from doname.network import NetworkError
from doname.providers import GoDaddyProvider, ProviderResult
from doname import rdap


class ValidationTests(unittest.TestCase):
    def test_unicode_multilevel_and_deduplication(self):
        self.assertEqual(exact_domain("  BÜCHER.CO.UK. "), "xn--bcher-kva.co.uk")
        self.assertEqual(exact_batch(["EXAMPLE.com", "example.com"]), ["example.com"])
        self.assertEqual(candidate_batch(["NOVA", "nova"], tlds(["com", "fr"])),
                         [("nova", ["nova.com", "nova.fr"])])

    def test_rejects_subdomains_urls_ips_ports_and_bad_suffixes(self):
        for value in ["www.example.com", "https://example.com", "example.com:443", "127.0.0.1", "example.invalidtld", "foo..com", "a\u200b.com"]:
            with self.subTest(value=value), self.assertRaises(InputError):
                exact_domain(value)
        with self.assertRaises(InputError):
            tlds(["bad.invalidtld"])
        with self.assertRaises(InputError):
            exact_batch(["example.com"] * 26)


class RDAPTests(unittest.TestCase):
    @patch.object(rdap, "_bootstrap", return_value={"com": "https://rdap.example.net"})
    @patch.object(rdap, "get_json", side_effect=NetworkError("http_404"))
    def test_404_is_only_not_found(self, *_):
        self.assertEqual(rdap.lookup("sample.com").status, "not_found")

    @patch.object(rdap, "_bootstrap", side_effect=NetworkError("timeout"))
    def test_bootstrap_failure_is_not_unsupported(self, *_):
        result = rdap.lookup("sample.com")
        self.assertEqual(result.status, "error")
        self.assertEqual(result.reason, "timeout")

    @patch.object(rdap, "_bootstrap", return_value={"com": "https://rdap.example.net"})
    @patch.object(rdap, "get_json", return_value={"objectClassName": "domain", "ldhName": "other.com"})
    def test_wrong_object_is_not_registration(self, *_):
        self.assertEqual(rdap.lookup("sample.com").status, "error")

    @patch.object(rdap, "_bootstrap", return_value={})
    def test_missing_coverage(self, *_):
        self.assertEqual(rdap.lookup("sample.com").status, "unsupported")


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = GoDaddyProvider("synthetic-token")

    @patch("doname.providers.get_json")
    def test_valid_prices_and_request_boundaries(self, get):
        get.return_value = {"domain": "sample.com", "available": True, "prices": [{"term": "YEAR", "period": 1,
            "price": {"value": 1299, "currencyCode": "EUR"}, "renewalPrice": {"value": 2199, "currencyCode": "EUR"}}]}
        result = self.provider.check("sample.com")
        self.assertEqual(result.evidence.status, "available")
        self.assertEqual(result.registration_price.amount, "12.99")
        self.assertEqual(result.renewal_price.amount, "21.99")
        args, kwargs = get.call_args
        self.assertTrue(args[0].startswith("https://api.godaddy.com/v3/domains/check-availability?"))
        self.assertNotIn("synthetic-token", args[0])
        self.assertIn("Bearer synthetic-token", kwargs["headers"]["Authorization"])

    @patch("doname.providers.get_json")
    def test_missing_or_malformed_available_is_error(self, get):
        for payload in [{"domain": "sample.com"}, {"domain": "sample.com", "available": "false"},
                        {"domain": "other.com", "available": False}]:
            get.return_value = payload
            self.assertEqual(self.provider.check("sample.com").evidence.status, "error")

    @patch("doname.providers.get_json", side_effect=NetworkError("http_429", 12))
    def test_quota_retains_retry_after(self, *_):
        result = self.provider.check("sample.com")
        self.assertEqual(result.evidence.status, "rate_limited")
        self.assertEqual(result.evidence.retry_after_seconds, 12)

    @patch("doname.providers.get_json", side_effect=NetworkError("timeout"))
    def test_timeout_is_not_unavailable(self, *_):
        self.assertEqual(self.provider.check("sample.com").evidence.status, "timeout")

    @patch("doname.providers.post_json")
    def test_batch_maps_by_domain_and_keeps_item_errors(self, post):
        post.return_value = {"items": [
            {"domain": "sample.com", "available": True, "prices": [{"term": "YEAR", "period": 1,
                "price": {"value": 1000, "currencyCode": "USD"}}]},
            {"domain": "sample.fr", "error": {"name": "UNSUPPORTED_TLD"}},
        ]}
        result = self.provider.check_many(["sample.com", "sample.fr"])
        self.assertEqual(result["sample.com"].evidence.status, "available")
        self.assertEqual(result["sample.fr"].evidence.status, "unsupported")
        args, kwargs = post.call_args
        self.assertEqual(args[0], self.provider.endpoint)
        self.assertEqual(kwargs["payload"] if "payload" in kwargs else args[1], {"domains": ["sample.com", "sample.fr"], "optimizeFor": "ACCURACY"})

    @patch("doname.providers.post_json", return_value={"items": [{"domain": "other.com", "available": False}]})
    def test_batch_wrong_domain_is_error(self, *_):
        self.assertEqual(self.provider.check_many(["sample.com"])["sample.com"].evidence.status, "error")


class ResolutionTests(unittest.TestCase):
    def test_nxdomain_and_rdap_404_never_confirm_availability(self):
        result = resolve("sample.com", Evidence("not_found", "RDAP"), None, Evidence("nxdomain", "DNS"))
        self.assertEqual(result.status, "not_found_in_registration_data")

    def test_provider_refusal_is_not_registration_or_conflict(self):
        result = resolve("sample.com", Evidence("not_found", "RDAP"), ProviderResult(Evidence("unavailable", "GoDaddy")))
        self.assertEqual(result.status, "unavailable_at_provider")

    def test_true_strong_conflict(self):
        result = resolve("sample.com", Evidence("registered", "RDAP"), ProviderResult(Evidence("available", "GoDaddy")))
        self.assertEqual(result.status, "conflict")

    def test_registered_works_without_provider(self):
        result = resolve("sample.com", Evidence("registered", "RDAP"), None)
        self.assertEqual(result.status, "registered")

    def test_provider_error_with_rdap_not_found_remains_unverified(self):
        result = resolve("sample.com", Evidence("not_found", "RDAP"), ProviderResult(Evidence("rate_limited", "GoDaddy")))
        self.assertEqual(result.status, "not_found_in_registration_data")
        self.assertEqual(result.registrability.status, "rate_limited")


if __name__ == "__main__":
    unittest.main()
