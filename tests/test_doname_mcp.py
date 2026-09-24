import unittest

from mcp import Client

from doname.mcp_server import UI_URI, mcp


class MCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_initialize_list_call_and_ui_resource(self):
        async with Client(mcp) as client:
            tools = await client.list_tools()
            descriptions = {tool.name: tool for tool in tools.tools}
            self.assertEqual(set(descriptions), {"capabilities", "check_domains", "screen_names"})
            self.assertTrue(descriptions["screen_names"].annotations.read_only_hint)
            self.assertEqual(descriptions["screen_names"].meta["ui"]["resourceUri"], UI_URI)
            self.assertIn("names", descriptions["screen_names"].input_schema["properties"])
            self.assertIsNotNone(descriptions["screen_names"].output_schema)
            capabilities = await client.call_tool("capabilities", {})
            self.assertFalse(capabilities.is_error)
            self.assertEqual(capabilities.structured_content["name"], "DoName")
            result = await client.call_tool("screen_names", {"names": ["nova"], "extensions": ["com", "fr"], "offline": True})
            self.assertFalse(result.is_error)
            self.assertEqual(result.structured_content["checked_domains"], 2)
            self.assertEqual(result.structured_content["excluded"][0]["match"], "unknown")
            resources = await client.list_resources()
            self.assertIn(UI_URI, {str(resource.uri) for resource in resources.resources})
            ui = await client.read_resource(UI_URI)
            self.assertEqual(ui.contents[0].mime_type, "text/html;profile=mcp-app")
            self.assertIn("ui/notifications/tool-result", ui.contents[0].text)


if __name__ == "__main__":
    unittest.main()
