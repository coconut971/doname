# DoName

DoName helps an AI turn a naming brief into a short selection with checked domain evidence. The AI invents names; DoName validates exact domains, checks registration data and, when configured, asks a registrar whether it offers registration and at what indicative price. DoName V1 has no purchase, reservation, DNS update, quote or checkout operation.

This repository is the **implementation branch**, not a published package or hosted plugin. The former IsDomainOK 2.1.0 code remains in Git history; the new Python package is `doname` 0.1.0. The MIT license and attribution remain intact.

## Try from a checkout

Python 3.10+ and [uv](https://docs.astral.sh/uv/) are needed for the portable local plugin configuration. From a clean clone of this branch:

```bash
uv sync --locked
uv run --locked doname capabilities
uv run --locked doname check example.com
uv run --locked doname screen nameone nametwo --extensions com fr --match all
```

`example.com` is a reserved example domain. The invented base names in the last command are illustrative, not live recommendations. For a fully offline check of validation and grouping, add `--offline`; that mode reports `not_verified` for every domain.

To get registrar availability and price data, create your own [GoDaddy Personal Access Token](https://developer.godaddy.com/en/docs/api-users/getting-started/authentication) with `domains.domain:read` and set `GODADDY_PAT` in the server process environment. Do not put it in a prompt, shell history, repository file or MCP tool arguments. Without a token, DoName remains useful through keyless RDAP, but cannot confirm purchase availability or price.

PowerShell example after the token has been securely placed in an environment variable by your normal secret manager:

```powershell
uv run --locked doname capabilities
uv run --locked doname screen nameone nametwo --extensions com fr --match all --budget 30 --currency EUR --available-only
```

The budget is compared to **each domain's total first registration term**, which can be more than one year for some TLDs. No currency conversion is performed. GoDaddy prices are indicative, specific to its account and market context, and can change. Renewal is separate and may be absent; the API renewal amount can reflect a discounted auto-renewal rate rather than a manual renewal price.

## The AI workflow

The [DoName naming skill](skills/doname-naming/SKILL.md) tells an agent to understand the brief, generate and judge a small pool itself, check names in a bounded batch, then explain a shortlist with sources and limits. The brief stays with the AI host. The domain provider receives only checked domains.

Three MCP tools cover the workflow:

| Tool | Purpose |
| --- | --- |
| `capabilities` | Provider state, keyless mode and limits, without exposing credentials. |
| `check_domains` | Batch check 1–25 exact registrable domains. Optional DNS observation and offline mode. |
| `screen_names` | Group up to 12 base names across extensions, enforce AND/OR, mandatory TLDs and budget, optionally show only matched names. |

For `.com` **and** `.fr`, use `extensions=["com","fr"]`, `match="all"`. For `.com` mandatory and `.fr` optional, use `match="any"`, `required_extensions=["com"]`. `available_only=true` shows only verified available domains within eligible names. Unknown prices cannot satisfy a budget. If a provider is absent, names can be shortlisted as unverified, never as confirmed available.

Results include source, `checked_at`, computed `age_seconds`, provider, reason and separate registration/renewal prices where supplied. `screen_names` also attaches a compact [MCP Apps](https://modelcontextprotocol.io/docs/extensions/apps) UI resource with cards and a local available-only filter for hosts that support it. The same tool returns complete structured data to hosts that render no UI.

## Meaning of the statuses

| Status | Meaning |
| --- | --- |
| `registered` | A correctly discovered RDAP service returned a validated domain object. |
| `not_found_in_registration_data` | RDAP returned 404; registrability is unconfirmed. |
| `available_at_provider` | The named provider offered registration at the checked time. |
| `unavailable_at_provider` | The provider did not offer registration; the domain is not necessarily registered. |
| `conflict` | RDAP returned a registered object while the provider offered registration. |
| `not_verified` | Evidence is missing, timed out, malformed, unsupported, or offline. |

DNS is optional and informational. NXDOMAIN says the DNS name was not found by that resolver. It never confirms registrability. DoName does not assign confidence percentages or claim trademark clearance.

## MCP transports and plugin packaging

Local stdio, with no application logs on stdout:

```bash
uv run --locked doname-mcp
```

Local Streamable HTTP on `127.0.0.1:8765/mcp`:

```bash
uv run --locked doname-mcp --http
```

The repository root has a portable [Agent Plugins](https://agent-plugins.org/specification) `plugin.json`, `mcp.json` and `skills/` package. Its `mcp.json` uses `uv` and the plugin root to start the local stdio server. `uv` must be installed on the host; first run may install locked Python dependencies. The package does not contain a hosted MCP address or a credential. A wheel carries the engine and UI; the plugin bundle carries source, lockfile, manifest and skill.

Host routes differ:

| Host | Route | Validated here |
| --- | --- | --- |
| MCP SDK client | Local stdio/in-process and loopback HTTP | Yes: initialize, list and call. |
| Codex CLI/IDE | Add stdio command or install local plugin package | Codex CLI called `capabilities` via an ephemeral MCP config; IDE not tried. |
| Claude Code | Add stdio command or project MCP configuration | Claude Code called `capabilities` via a temporary MCP config. |
| ChatGPT desktop | Local plugin/MCP support depends on surface and policy | Not tried. |
| ChatGPT web | HTTPS Streamable HTTP endpoint or private Secure MCP Tunnel for development | No DoName remote deployment or host test. |
| Other MCP Apps hosts | MCP tool plus `ui://` resource | Resource contract tested; visual host rendering not yet tried. |

Codex: `codex mcp add doname -- uv run --locked --project <checkout-path> -- python -m doname.mcp_server`. Claude Code: `claude mcp add doname -- uv run --locked --project <checkout-path> -- python -m doname.mcp_server`. Replace `<checkout-path>` with the absolute path to this checkout. Both commands are examples from their current [Codex](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) and [Claude Code](https://code.claude.com/docs/en/mcp) MCP syntax; no installation in those hosts is claimed yet.

For ChatGPT web, a localhost endpoint and `mcp.json` are insufficient. A future DoName-operated service needs a stable public HTTPS `/mcp`, server-side provider credentials, authentication/authorization, rate limiting, log privacy, domain verification and plugin review. The [official OpenAI plugin guide](https://developers.openai.com/plugins/deploy/connect-chatgpt) distinguishes a private development tunnel from public submission. This repository does not deploy or publish such a service.

## Privacy and network limits

No search history, database or telemetry is implemented. No name brief is sent to the registrar. Network checks disclose each checked domain to the selected RDAP service and, if configured, GoDaddy. RDAP bootstrap metadata comes from IANA. Optional DNS observations disclose domains to the machine's resolver. Offline mode performs no domain network lookup. DoName never visits the candidate's website or arbitrary model-supplied URLs.

Requests, response bodies, batch size, concurrency and total duration are bounded. API redirects are rejected; provider URLs are fixed; RDAP URLs are selected from IANA bootstrap data and screened for HTTPS/public hostnames. These application controls do not inspect the AI host, reverse proxy or infrastructure logs. A public service requires its own privacy and abuse review.

## Development

```bash
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
uv run --locked python scripts/validate_manifests.py
uv run --locked python scripts/benchmark.py
node scripts/ui_smoke.js
uv build
uv run --locked python scripts/build_plugin.py
uv run --locked python scripts/smoke_bundle.py
```

The manifest validator uses local copies of the versioned Agent Plugins schemas and checks their pinned hashes; it sends no search data. Public CI runs the tests and packaging smoke on Linux and Windows, but never calls a live registrar. A credentialed run uses the separate [private GoDaddy probe](docs/doname/LIVE_PROVIDER_TEST.md). The prepared [ChatGPT developer-mode test](docs/doname/CHATGPT_DEV_TEST.md) uses a private tunnel and has not yet been performed.

See [project memory](docs/doname/PROJECT.md) for decisions, measured validation and remaining work. The original [implementation brief](docs/doname/CODEX_PROMPT.md) is preserved as a historical reference.
