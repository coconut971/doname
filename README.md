# DoName

**Domain research for AI naming workflows.** DoName helps an AI turn a naming brief into a shortlist backed by current domain evidence. The AI invents and judges names; DoName checks exact domains in batches, keeps RDAP and registrar results separate, and applies extension and budget constraints. When configured, GoDaddy supplies indicative registration and renewal prices.

DoName 0.1.0 is a **local, non-transactional MCP plugin**. It does not buy, reserve, transfer or modify domains. The source and plugin bundle can be distributed without a shared credential or DoName account. There is no hosted DoName service or PyPI publication. The former IsDomainOK code and its `v1.0.0` tag remain in Git history; DoName uses `doname-v*` release tags. The MIT license and attribution remain intact.

| What it can establish | What it cannot establish |
| --- | --- |
| A valid RDAP domain object shows registration. A definitive GoDaddy availability response shows what that provider offered at the checked time. | A DNS NXDOMAIN or RDAP 404 is **not** purchase availability. Registrar results and prices can change before checkout. DoName does not check trademarks. |

## Try from a checkout

Python 3.10+ and [uv](https://docs.astral.sh/uv/) are needed for the portable local plugin configuration. From a clean clone or extracted source release:

```bash
uv sync --locked
uv run --locked doname capabilities
uv run --locked doname check example.com
uv run --locked doname screen nameone nametwo --extensions com fr --match all
```

`example.com` is a reserved example domain. The invented base names are illustrative, not live recommendations. For a fully offline check of validation and grouping, add `--offline`; that mode reports `not_verified` for every domain.

To get registrar availability and price data, create your own [GoDaddy Personal Access Token](https://developer.godaddy.com/en/docs/api-users/getting-started/authentication) with `domains.domain:read` and set `GODADDY_PAT` in the server process environment. Do not put it in a prompt, shell history, repository file or MCP tool arguments. Without a token, DoName remains useful through keyless RDAP, but cannot confirm purchase availability or price.

PowerShell example after the token has been securely placed in an environment variable by your normal secret manager:

```powershell
uv run --locked doname capabilities
uv run --locked doname screen nameone nametwo --extensions com fr --match all --budget 30 --currency USD --available-only
```

Use the currency actually returned by your provider account; the USD example is illustrative. The budget is compared to **each domain's total first registration term**, which can be more than one year for some TLDs. No currency conversion is performed. GoDaddy prices are indicative, specific to its account and market context, and can change. Renewal is separate and may be absent; the API renewal amount can reflect a discounted auto-renewal rate rather than a manual renewal price.

## The AI workflow

The [DoName naming skill](skills/doname-naming/SKILL.md) tells an agent to understand the brief, generate and judge a small pool itself, check names in a bounded batch, then explain a shortlist with sources and limits. The brief stays with the AI host. The domain provider receives only checked domains.

Three MCP tools cover the workflow:

| Tool | Purpose |
| --- | --- |
| `capabilities` | Provider state, keyless mode and limits, without exposing credentials. |
| `check_domains` | Batch check 1–25 exact registrable domains. Optional DNS observation and offline mode. |
| `screen_names` | Group up to 12 base names across extensions, enforce AND/OR, mandatory TLDs and budget, optionally show only matched names. |

When no extensions are supplied, name screening checks `.com`, `.fr`, `.ai`, `.io` and `.app` using `match="any"`. For `.com` **and** `.fr`, use `extensions=["com","fr"]`, `match="all"`. For `.com` mandatory and `.fr` optional, use `match="any"`, `required_extensions=["com"]`. `available_only=true` shows only domains with definitive provider availability within eligible names. Unknown prices cannot satisfy a budget. If a provider is absent, names can be shortlisted as unverified, never as confirmed available.

Results include source, `checked_at`, computed `age_seconds`, provider, reason and separate registration/renewal prices where supplied. `screen_names` attaches a compact [MCP Apps](https://modelcontextprotocol.io/docs/extensions/apps) result card when supported. The AI decides which candidates to request; the card has no manual availability filter. Hosts advertising MCP Apps server-tool calls also get a quick search: a base name checks `.com`, `.fr`, `.ai`, `.io` and `.app`, while a full domain such as `lune.ai` checks that exact domain. Name search shows provider-confirmed available extensions only; freshness and source evidence remain in the expandable details. Hosts without server-tool support retain the full text/structured flow.

## Meaning of the statuses

| Status | Meaning |
| --- | --- |
| `registered` | A correctly discovered RDAP service returned a validated domain object. |
| `not_found_in_registration_data` | RDAP returned 404; registrability is unconfirmed. |
| `available_at_provider` | The named provider returned definitive availability at the checked time. It is not a checkout guarantee. |
| `unavailable_at_provider` | The provider did not offer registration; the domain is not necessarily registered. |
| `conflict` | RDAP returned a registered object while the provider offered registration. |
| `not_verified` | Evidence is missing, timed out, malformed, unsupported, non-definitive, or offline. |

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

The repository root has a portable [Agent Plugins](https://agent-plugins.org/specification) `plugin.json`, `mcp.json` and `skills/` package. Its `mcp.json` uses `uv` and the plugin root to start the local stdio server. `uv` must be installed on the host; first run may install locked Python dependencies. The package does not contain a hosted MCP address or a credential. A wheel carries the engine and UI; the [GitHub release](https://github.com/coconut971/isdomainok/releases) provides a plugin ZIP with source, lockfile, manifest and skill.

Host routes differ:

| Host | Route | Validated here |
| --- | --- | --- |
| MCP SDK client | Local stdio/in-process and loopback HTTP | Yes: initialize, list and call. |
| Codex CLI/IDE | Add stdio command or install local plugin package | Codex CLI called `capabilities` via an ephemeral MCP config; IDE not tried. |
| Claude Code | Add stdio command or project MCP configuration | Claude Code called `capabilities` via a temporary MCP config. |
| ChatGPT desktop | Local plugin/MCP support depends on surface and policy | Not tried. |
| ChatGPT web | Private Secure MCP Tunnel in developer mode | **Previously tested:** the v2 cards rendered in offline, keyless RDAP and live GoDaddy calls. The v3 card design and in-card domain check are pending a new host test. The temporary local tunnel was stopped afterward. |
| Other MCP Apps hosts | MCP tool plus `ui://` resource | Resource contract tested; visual rendering not tried elsewhere. |

Codex: `codex mcp add doname -- uv run --locked --project <checkout-path> -- python -m doname.mcp_server`. Claude Code: `claude mcp add doname -- uv run --locked --project <checkout-path> -- python -m doname.mcp_server`. Replace `<checkout-path>` with the absolute path to this checkout. Both routes were tested with `capabilities` through temporary configurations; no global host configuration was changed.

For ChatGPT web, a localhost endpoint and `mcp.json` are insufficient. The [private tunnel test](docs/doname/CHATGPT_DEV_TEST.md) proved the MCP Apps flow in a real conversation. A public ChatGPT plugin would need a stable public HTTPS `/mcp`, server-side provider credentials, authentication/authorization, rate limiting, log privacy, domain verification and plugin review. The [official OpenAI plugin guide](https://developers.openai.com/plugins/deploy/connect-chatgpt) distinguishes a private development tunnel from public submission. This repository does not deploy or publish such a service.

## Privacy and network limits

No search history, database or telemetry is implemented. No name brief is sent to the registrar. Network checks disclose each checked domain to the selected RDAP service and, if configured, GoDaddy. RDAP bootstrap metadata comes from IANA. Optional DNS observations disclose domains to the machine's resolver. Offline mode performs no domain network lookup. DoName never visits the candidate's website or arbitrary model-supplied URLs.

Requests, response bodies, batch size, concurrency and total duration are bounded. API redirects are rejected; provider URLs are fixed; RDAP URLs are selected from IANA bootstrap data and screened for HTTPS/public hostnames. These application controls do not inspect the AI host, reverse proxy or infrastructure logs. A public service requires its own privacy and abuse review.

## Local release checks

```bash
python3 scripts/release_check.py
```

On Windows, use `py -3.13 scripts/release_check.py`; add `--python 3.10 --python 3.13` to exercise both versions when installed. The script needs Python 3.10+, `uv` and Node.js. It checks version consistency and the lockfile, runs the Python tests, validates the manifests, smokes the MCP Apps lifecycle, builds the plugin ZIP and Python distributions, audits their contents, and starts the extracted bundle to discover and call its MCP tools. It removes `GODADDY_PAT` and the tunnel key from child environments and never calls a live registrar. The GitHub Actions workflow is retained for repositories where Actions is available, but **this repository's release process uses the local check**.

The [private GoDaddy probe](docs/doname/LIVE_PROVIDER_TEST.md) and [ChatGPT developer-mode test](docs/doname/CHATGPT_DEV_TEST.md) were also performed with public controls and synthetic candidates. Neither stores credentials or raw results in Git. See [security and privacy notes](SECURITY.md) before self-hosting. The optional [synthetic benchmark](scripts/benchmark.py) excludes network and model latency.

See [project memory](docs/doname/PROJECT.md) for decisions, measured validation and remaining work. The original [implementation brief](docs/doname/CODEX_PROMPT.md) is preserved as a historical reference.
