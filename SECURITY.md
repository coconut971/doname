# Security and privacy

DoName V1 runs locally by default. It has no search database, analytics or telemetry. The host AI still sees the conversation, and live checks send each queried domain to the selected RDAP service and, when configured, GoDaddy. DNS checks are optional and contact the machine's resolver. DoName never sends the naming brief to a registrar.

## Credentials

- Use a GoDaddy PAT with only `domains.domain:read` for ongoing use. Supply it as `GODADDY_PAT` to the local server process; never place it in prompts, tool arguments, Git files, screenshots or issue reports.
- The plugin bundle and Python distributions contain no credentials. The local release check removes `GODADDY_PAT` and `CONTROL_PLANE_API_KEY` from its child processes.
- Rotate any PAT that was created with broader permissions for a temporary test. Availability and pricing checks do not require DNS or registration write scopes.

## Network exposure

The HTTP transport binds to `127.0.0.1` by default. It is not an authenticated public service. A public deployment needs authentication, rate limiting, request isolation and a review of proxy, host and application logs before accepting private searches. A private OpenAI Secure MCP Tunnel test is not such a deployment.

## Reporting

Please do not post credentials, private domain candidates, raw provider responses or exploit details in a public issue. Use GitHub's private vulnerability reporting for this repository if available, or contact the maintainer privately through their GitHub profile.

Supported release line: DoName 0.1.x. The historical IsDomainOK code is retained in Git history and is not part of the current package.
