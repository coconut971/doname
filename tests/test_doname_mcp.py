import unittest
from unittest.mock import patch

from mcp import Client

from doname.mcp_server import UI_URI, mcp
from doname.models import DomainResult, Evidence, Price


class MCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_initialize_list_call_and_ui_resource(self):
        async with Client(mcp) as client:
            tools = await client.list_tools()
            descriptions = {tool.name: tool for tool in tools.tools}
            self.assertEqual(set(descriptions), {"capabilities", "check_domains", "screen_names"})
            self.assertTrue(descriptions["screen_names"].annotations.read_only_hint)
            self.assertEqual(descriptions["screen_names"].meta["ui"]["resourceUri"], UI_URI)
            self.assertEqual(UI_URI, "ui://doname/cards/v3.html")
            self.assertIn("names", descriptions["screen_names"].input_schema["properties"])
            self.assertIsNotNone(descriptions["screen_names"].output_schema)
            self.assertIn("DomainOutput", descriptions["screen_names"].output_schema["$defs"])
            capabilities = await client.call_tool("capabilities", {})
            self.assertFalse(capabilities.is_error)
            self.assertEqual(capabilities.structured_content["name"], "DoName")
            result = await client.call_tool("screen_names", {"names": ["nova"], "extensions": ["com", "fr"], "offline": True})
            self.assertFalse(result.is_error)
            self.assertEqual(result.structured_content["checked_domains"], 2)
            self.assertEqual(result.structured_content["excluded"][0]["match"], "unknown")
            self.assertIn("nova.com: not_verified", result.content[0].text)
            default_search = await client.call_tool("screen_names", {"names": ["lune"], "offline": True})
            self.assertFalse(default_search.is_error)
            self.assertEqual(default_search.structured_content["constraints"]["extensions"], ["com", "fr", "ai", "io", "app"])
            self.assertEqual(default_search.structured_content["constraints"]["match"], "any")
            self.assertEqual(default_search.structured_content["checked_domains"], 5)
            resources = await client.list_resources()
            self.assertIn(UI_URI, {str(resource.uri) for resource in resources.resources})
            ui = await client.read_resource(UI_URI)
            self.assertEqual(ui.contents[0].mime_type, "text/html;profile=mcp-app")
            self.assertIn("ui/notifications/tool-result", ui.contents[0].text)

    async def test_text_fallback_preserves_both_sources_and_price(self):
        registration = Evidence("not_found", "registry.example")
        provider = Evidence("available", "GoDaddy")
        row = DomainResult("sample.com", "available_at_provider", "provider_reports_available",
                           registration, provider, registration_price=Price("12.00", "EUR", 1,
                           "registration", "GoDaddy", provider.checked_at))
        with patch("doname.mcp_server.engine_check", return_value=[row]):
            async with Client(mcp) as client:
                result = await client.call_tool("check_domains", {"domains": ["sample.com"]})
        self.assertFalse(result.is_error)
        self.assertIn("RDAP not_found via registry.example", result.content[0].text)
        self.assertIn("provider available via GoDaddy", result.content[0].text)
        self.assertIn("register 12.00 EUR", result.content[0].text)


if __name__ == "__main__":
    unittest.main()
