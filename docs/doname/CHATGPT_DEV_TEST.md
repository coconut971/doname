# Private ChatGPT MCP Apps test: prepared, not performed

The shortest supported test path for DoName is an OpenAI [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) to its local stdio server. The tunnel is for a private developer-mode connection, not plugin publication. It needs a Platform tunnel ID, a runtime API key, tunnel permissions and access to ChatGPT developer mode in the target workspace. The tunnel must be associated with that ChatGPT workspace. None of these resources has been created for DoName yet.

## Local preparation

From a checkout of `implementation/doname-v1`, install the locked dependencies and verify the local server before involving ChatGPT:

```powershell
uv sync --locked
uv run --locked doname capabilities
uv run --locked python scripts/build_plugin.py
uv run --locked python scripts/smoke_bundle.py
```

The first visual test can use keyless/offline synthetic names. A GoDaddy credential is not required to verify card rendering. If a provider credential is later used, pass it to the local server process through a secret manager. Never place it in ChatGPT prompts, tunnel command arguments, repository files or screenshots.

## Private tunnel and ChatGPT

1. In [Platform tunnel settings](https://platform.openai.com/settings/organization/tunnels), create a tunnel associated with the target ChatGPT workspace. Ensure the operator has Tunnels Read + Manage to create it and Read + Use to run/select it. Obtain the current `tunnel-client` from Platform settings and follow `tunnel-client help quickstart` for its installed version.
2. Provide `CONTROL_PLANE_API_KEY` to the `tunnel-client` process through a secret manager. From the repository root, use the [documented local stdio profile](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) with a DoName command. Replace the example path and tunnel ID with the actual values; do not copy secrets into the command:

   ```powershell
   tunnel-client init --sample sample_mcp_stdio_local --profile doname-local --tunnel-id <tunnel_id> --mcp-command "uv run --locked --project C:/Dev/DoName -- python -m doname.mcp_server"
   tunnel-client doctor --profile doname-local --explain
   tunnel-client run --profile doname-local
   ```

3. In ChatGPT, enable **Settings → Security and login → Developer mode** if the workspace permits it. Go to **Plugins → +**, select **Tunnel**, choose that tunnel or enter its ID, and confirm the three discovered tools and UI metadata. These are the current [OpenAI developer-mode connection steps](https://developers.openai.com/plugins/deploy/connect-chatgpt).
4. Start a new conversation with the developer-mode connection enabled. First ask for `screen_names` with invented names such as `donamealpha` and `donamebeta`, `.com` and `.fr`, and `offline=true`; no domain lookup is made in that mode. Confirm the cards appear, the available-only filter behaves, and the text/structured tool result remains useful if the host does not render the View. Then run a keyless synthetic live check if wanted. Do not submit real user search briefs or private candidates during this integration test.
5. After UI changes, restart the server/tunnel, refresh the MCP connection in ChatGPT and start a new conversation. Record whether the View initialized, showed the tool result and closed cleanly; keep screenshots and tool traces outside the public repository. Stop `tunnel-client` and remove the temporary developer-mode connection/tunnel when finished.

ChatGPT may still retain app invocation data under the workspace's normal logging and compliance policy. DoName's absence of application search telemetry does not control host or tunnel administration logs. The [OpenAI tunnel guide](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) describes this boundary.

A public HTTPS Streamable HTTP endpoint is an alternative for developer-mode testing, but `http://127.0.0.1:8765/mcp` is not reachable from ChatGPT directly. Public plugin submission needs a stable, publicly reachable HTTPS endpoint and separate review; this guide performs neither deployment nor publication.
