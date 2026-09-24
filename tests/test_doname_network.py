import io
import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from doname.engine import check_domains
from doname.models import DomainResult, Evidence, Price
from doname.network import NetworkError, request_json
from doname.providers import GoDaddyProvider
from scripts.live_godaddy_probe import main as live_probe, summarize


class NetworkBoundaryTests(unittest.TestCase):
    def test_rejects_non_https_and_oversized_response(self):
        with self.assertRaises(NetworkError):
            request_json("http://127.0.0.1/private")
        with patch("doname.network._OPENER.open", return_value=io.BytesIO(b"{\"a\":1}")):
            with self.assertRaises(NetworkError) as caught:
                request_json("https://example.net/", max_bytes=4)
        self.assertEqual(caught.exception.code, "response_too_large")

    def test_redirect_is_an_error_not_followed(self):
        redirect = HTTPError("https://example.net/", 302, "redirect", {}, None)
        with patch("doname.network._OPENER.open", side_effect=redirect):
            with self.assertRaises(NetworkError) as caught:
                request_json("https://example.net/")
        self.assertEqual(caught.exception.code, "http_302")

    def test_invalid_domain_never_reaches_network(self):
        with patch("doname.engine.rdap.lookup") as rdap:
            with self.assertRaises(ValueError):
                check_domains(["https://example.com"])
            rdap.assert_not_called()

    def test_token_absent_from_error_evidence(self):
        token = "synthetic-secret-do-not-print"
        with patch("doname.providers.post_json", side_effect=NetworkError("http_429", 9)):
            result = GoDaddyProvider(token).check_many(["sample.com"])
        self.assertNotIn(token, json.dumps(result["sample.com"].evidence.to_dict()))

    def test_live_probe_output_omits_generated_domain(self):
        provider = Evidence("available", "GoDaddy")
        row = DomainResult("doname-probe-secret.com", "available_at_provider", "provider_reports_available",
                           Evidence("not_found", "RDAP"), provider,
                           registration_price=Price("12.00", "EUR", 1, "registration", "GoDaddy", provider.checked_at))
        output = json.dumps(summarize("candidate_com", "com", row))
        self.assertNotIn(row.domain, output)
        self.assertIn("12.00", output)

    def test_live_probe_without_token_makes_no_request(self):
        with patch.dict(os.environ, {"GODADDY_PAT": ""}), patch("scripts.live_godaddy_probe.check_domains") as check:
            with self.assertRaises(SystemExit):
                live_probe()
            check.assert_not_called()


if __name__ == "__main__":
    unittest.main()
