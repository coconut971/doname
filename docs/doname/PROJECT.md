# DoName — project memory and refoundation brief

Date: 2026-09-24. Status: DoName 0.1.0 source and local plugin bundle released on GitHub as `doname-v0.1.0`; no public hosted service.

Repository inspected: `coconut971/isdomainok`, public. Baseline: `main` at `80fea7d9a8cb13fc1509286d7c254c47041ba4b1` (IsDomainOK 2.1.0). Keep this history. **DoName V1** names the new product milestone; do not silently downgrade an already published package's version.

## 1. Explicit user decisions

The name is **DoName**, spelled D-O-N-A-M-E. Rebuild the current project around an installable AI experience for ChatGPT, Codex, Claude and other compatible hosts, rather than a DNS command-line utility. The user wants a finished, fast, clear and simple product, not unnecessary size. Source must be public; searches and operational data must remain private.

**V1 is non-transactional, not disconnected from the market.** It should already be able to use at least one real read-only availability/pricing source so an AI can obtain current registrability and price information instead of guessing. It may show the provider, registration price, renewal price when available, freshness, unsupported TLDs and an outbound link to a registrar or broker. DoName itself must not charge, receive a commission, register a domain, run checkout, mutate DNS or silently act on behalf of the user in V1. Commercial relationships, affiliate economics, reseller/registrar actions and in-chat purchasing belong to a later explicitly approved phase.

Design DoName around a small provider abstraction from the start so the engine is not permanently coupled to GoDaddy, Namecheap or another single registrar. Codex should investigate current registrar/registry/reseller APIs and choose a viable first V1 provider based on access, coverage, data quality, terms, pricing fields and maintainability; do not assume a partnership exists.

Existing principles to preserve: MIT license, useful local/self-hosted execution, a keyless evidence mode, no telemetry by default, no automatic domain purchase, and no mandatory model API. A public ChatGPT plugin may require a DoName-operated remote MCP service and server-side provider credentials; that hosted path must be cleanly separated from local/self-hosted use and must not make local use depend on the hosted service.

## 2. Architecture direction

**Keep the existing repository; refound the product without deleting its history.** There is already a separable Python core, MCP server, skill and tests. Keep what is demonstrably correct, replace what is not. A new repository is not presently justified. The remote name has not been changed to `doname`; naming/package availability and links require a separate release check.

Ship a **plugin**, composed of a reusable MCP engine and a portable naming skill, with thin host-specific packaging. The skill guides how to work; the MCP tools obtain live evidence. A skill alone cannot verify live domain status. The CLI remains a development/diagnostic entry point, not the main product presentation.

Start from Python unless a concrete installation, SDK or maintenance comparison supports changing it. Do not introduce a mandatory model API, vector database, microservices or a large web dashboard. **Compact chat-native result UI is part of the V1 product where the host supports MCP Apps/UI resources**: domain cards, availability state, provider/source, prices, freshness and a few useful actions/filters. The text/structured-data path remains first-class for hosts without that UI capability.

Local stdio and an optional self-hostable Streamable HTTP transport should share the same engine. Local use must not depend on a DoName-operated server. ChatGPT web needs its supported remote/plugin connection; a local configuration file is not a web integration. Current OpenAI documentation also provides a Secure MCP Tunnel for private development/testing. Public plugin submission is a separate step requiring a public HTTPS MCP endpoint; a tunnel test is not public distribution. Host permissions and review rules remain applicable.

## 3. Product promise

> Help an AI turn a naming brief into a small, useful and honestly checked selection of domain candidates — without turning the conversation into a shop.

Example workflow, not a live domain recommendation: the user asks for a short bilingual name and requires both `.com` and `.fr`. The host AI generates candidates; DoName normalizes them, validates domain syntax, checks evidence in bounded batches, groups results by name and applies the requested AND condition across extensions. The AI then proposes a few names with reasons and precise verification limits. A follow-up changes a preference without repeating fresh checks unnecessarily.

Generating alternatives alone is not a defensible differentiator: the host AI can already do that. The improvement should be measurable in constraint handling, evidence quality, usable grouping, setup effort, call count and token cost. Do not claim to have beaten Namecheap without comparable measurements. The Namecheap connector inspected in this session exposes availability/pricing batch checks for up to 20 domains; this is not an exhaustive audit of Namecheap's products or underlying API limits.

Suggested small tool surface, with final names left to implementation: capabilities/diagnostics, checking exact domains, screening candidate names across extensions. Return concise summaries and structured evidence. Avoid a tool per DNS record and avoid duplicating tools with almost identical roles.

## 4. Data truth is the core feature

Keep three concepts separate: registration evidence, registrability at a given source/time, and DNS observations. An authoritative-looking source must still have its identity and response validated.

- DNS NXDOMAIN: no such DNS name was found by that check; not proof that the name can be bought.
- RDAP 404 from the correctly discovered service: no matching object was returned; not guaranteed availability.
- Validated RDAP domain object: evidence of registration, with an observation timestamp.
- Registrar/registry availability response: a scoped, timestamped registrability signal; not a guarantee until registration succeeds.
- Registrar refusal: unavailable through that source, with its actual reason where supplied; not automatically registered.
- Timeout, rate limit, missing coverage, malformed payload and conflicting strong evidence: explicitly distinct outcomes, never converted into a positive result.

Suggested user-facing labels: registered, not found in registration data, available according to a named source, unavailable according to a named source, not verified, conflicting evidence. The exact machine schema is an implementation choice; it must preserve these distinctions and include source, checked time, freshness and reasons. Do not count correlated sources as independent votes or manufacture confidence percentages.

A useful keyless V1 can eliminate confirmed registrations and return clearly qualified candidates. **It cannot promise the same certainty as a direct registrability service for every extension.** In addition, the primary V1 experience should integrate at least one documented real read-only provider for current availability and pricing when technically and contractually viable. Provider credentials may be supplied by the self-hoster or held server-side by an operated DoName endpoint; never expose them to the model or user.

Registration price and renewal price should be represented separately when the source supplies them. A provider result is scoped to that provider and observation time, not universal truth. Unknown price means budget not verified, not free or within budget. Full multi-registrar price comparison is desirable when cleanly supportable but is not worth delaying a solid first provider. Locked quotes, purchase actions and uncontrolled resale-page crawling are not V1 requirements. Domain checks are not trademark clearance.

## 5. Privacy boundary

Public: source, synthetic tests, packaging, documentation, public reference metadata. Private: user briefs, candidate lists, query history, credentials and infrastructure request traces.

Do not persist search payloads by default. Scope any short-lived candidate cache to its user/session or local process; use an explicit retention limit and never put it into public CI artifacts. Public reference caches may be shared. Provider errors and access logs must not echo secrets or query payloads. Review application, proxy, host, monitoring and CI logging separately; a code flag cannot guarantee infrastructure privacy.

Only the domain required for a query goes to the chosen provider, never the business brief. Do not contact target websites by default. Local execution removes a mandatory DoName intermediary, not the visibility of the host AI, DNS resolver or RDAP/provider service. Document each actual recipient and an offline mode that makes no live-status claim.

## 6. Static audit at the baseline

This is a focused source review through the GitHub connector, not a penetration test or complete history/secret audit. The runtime could not resolve GitHub for cloning; the repository test suite and actual AI-host installations were not executed here. No live customer domains were submitted to Namecheap.

**A. Incorrect positive availability.** `okitsok/rdap.py:lookup_domain` maps HTTP 404 to `available`. `okitsok/core.py:resolve_consensus` can turn this plus DNS absence into `available/high` without a registrar. Replace the evidence model and add a regression case.

**B. Incorrect registration/refusal equivalence.** `resolve_consensus` maps a false registrar availability result to `registered`. It treats RDAP absence plus provider refusal as a conflict, even though an unregistered name can be refused. Retain refusal reason and source scope instead. `pricing.py` also uses `bool(data.get('available'))`, so a missing or malformed field can become false: validate response types.

**C. Weak input/network boundaries.** `mcp_server.py:check_domain` essentially checks that input is nonempty and contains a dot. `core.py:expand_domains` has no robust registrable-domain validation. `market.py:inspect_sale_page` fetches user-derived URLs and follows redirects without explicit private-network protections. This is a risk identified by inspection, not a demonstrated exploitation. Remove target-page scanning from V1; harden any remaining outbound HTTP paths and test them with mocks before remote exposure.

**D. Unbounded work despite limited threads.** `check_domains` caps workers but creates a future for every expanded domain. The MCP inputs have no explicit collection limits; per-domain DNS, RDAP and provider steps are sequential. Introduce batch bounds, per-provider quotas, total deadlines, response caps, cancellation and partial results. The RDAP bootstrap cache has no freshness policy and conflates bootstrap-fetch failure with unsupported coverage.

**E. Incomplete AI-facing product.** MCP and an Agent Skill already exist. The current surface remains closely coupled to GoDaddy and legacy checks. Explicit tool annotations/output contracts, complete packaging, grouped naming constraints and real host validation need work. `screen_names` returns a flat domain list rather than implementing extension-bundle constraints. Avoid unconverted cross-currency numeric sorting if optional prices survive.

**F. Documentation drift.** README, packaging and `PROJECT.md` mix IsDomainOK and okitsok identities. The old project document insists on DNS-only operation and describes package distribution differently from README, which says publication is not established. Do not copy those assertions into the new product. Existing tests describe the old semantics; preserving every old assertion is not a success criterion.

Useful components: separated core modules, batch orchestration, read-only intent, source separation in results, optional credentials, MCP entry point and skill concept. None is automatically production-ready merely because it already exists.

## 7. Delivery and V2 boundary

Deliver in reviewable increments: evidence/validation corrections; provider abstraction plus at least one viable live read-only availability/pricing adapter; useful naming workflow; MCP/plugin packaging; compact MCP App/UI where supported; privacy/performance/installation checks; release preparation. Complete real vertical slices, not only plans and stubs. Public release requires an actual tested artifact and a truthful compatibility matrix. A self-host recipe is not an operated service or a directory listing.

V1 may send the user to an external registrar or marketplace page, but DoName itself does not process the transaction and should not depend on affiliate revenue or a commercial agreement. For already-registered domains, expose only grounded aftermarket/broker information from supported sources; if no public sale/price exists, say so instead of inventing one.

V2 may add multiple commercial provider agreements, deeper registration/renewal comparison, affiliate/reseller economics, broker integrations and explicit user-authorized purchase/registration actions. Payment handling or delegated purchase is not approved by this planning document. Keep V1's research engine reusable rather than building empty V2 infrastructure now.

## 8. Primary documentation checked on 2026-09-24

Recheck these during implementation; formats and platform permissions can change.

- OpenAI plugin overview and packaging: https://developers.openai.com/plugins and https://developers.openai.com/plugins/build/plugins
- OpenAI MCP implementation: https://developers.openai.com/plugins/build/mcp-server
- OpenAI testing, tunnels and publication boundary: https://developers.openai.com/plugins/deploy/connect-chatgpt
- Codex/desktop MCP and the distinction from ChatGPT web: https://developers.openai.com/codex/mcp
- Claude Code MCP: https://code.claude.com/docs/en/mcp
- Claude plugin submission to OpenAI: https://developers.openai.com/plugins/guides/submit-claude-plugin
- MCP transports: https://modelcontextprotocol.io/specification/2026-07-28/basic/transports
- RDAP HTTP semantics, especially negative responses and rate limits: RFC 7480, sections 5.3 and 5.5, https://www.rfc-editor.org/rfc/rfc7480.html
- Namecheap's separate domain-check API documentation: https://www.namecheap.com/support/api/methods/domains/check/

## 9. Decision log

2026-09-24 — User decisions: DoName name; AI/plugin-first refoundation; public source/private searches; non-commercial V1; future commercial V2; autonomous Codex implementation within firm boundaries.

2026-09-24 — Architecture recommendation: keep repository/history; shared MCP engine plus skill and thin host packaging; local/self-hosted support plus a separate remote path for public ChatGPT integration; retain MIT; prioritize evidence correctness over exaggerated availability claims. Language and detailed module structure remain open to a justified implementation decision.

2026-09-24 — V1 refinement after inspecting the installed Namecheap plugin: DoName V1 should already use real read-only market data for current domain availability and pricing, while remaining non-transactional. Design a provider-neutral interface, select at least one viable live provider, show registration and renewal price separately when available, and support compact in-chat UI on hosts that implement MCP Apps/UI resources. Purchase, commissions and commercial provider economics remain outside V1.

## 10. Implementation record

2026-09-24 — First vertical slice committed as `05d4abe` on `implementation/doname-v1`. A new Python `doname` package replaces the old public package identity without deleting Git history. The engine validates registrable domains with an offline bundled public suffix list and IDNA, caps a call at 25 domains, separates RDAP registration, provider registrability and optional DNS observations, and resolves statuses without converting NXDOMAIN/RDAP 404/provider refusal into registration or availability. The provider protocol supports batch reads. GoDaddy v3 is the first adapter because its documented read-only batch endpoint accepts 1–25 domains and returns indicative registration/renewal prices. It uses `GODADDY_PAT` only on the server side. No credential was present for a live GoDaddy call.

The naming flow groups extensions per candidate, applies all/any plus mandatory extension and budget constraints, and can hide nonmatching names. MCP SDK v2 exposes three tools over stdio and loopback Streamable HTTP, with a compact MCP Apps UI resource for `screen_names`; the structured response remains complete. Twenty-five new automated tests passed. An SDK MCP in-process exchange, a real loopback HTTP MCP exchange and a live keyless RDAP check of `example.com` succeeded. That RDAP check returned `registered`; it did not test provider availability or price. No ChatGPT or Claude UI host was tested yet.

Current limits: GoDaddy prices are indicative and scoped to its account/market context; renewal may be omitted. `.fr` coverage and actual provider credentials remain unverified. The keyless path confirms registrations or reports absence of an RDAP object, never registrability. No production endpoint, public plugin submission or package publication exists. Hosting requires explicit operations work, an authentication and abuse-control boundary, and a privacy review of proxy/application logs.

### Provider choice rechecked against official documentation

| Source | Documented access and signal | Decision |
| --- | --- | --- |
| [GoDaddy Domains v3](https://developer.godaddy.com/en/docs/references/rest/domains/v3/discovery) | Personal Access Token; read-only `POST /check-availability` checks 1–25 domains and returns availability plus indicative registration and renewal price per term; 60 requests/minute per credential. | First V1 adapter. One provider batch per DoName call; `ACCURACY`; read scope only. The code has mock contract tests; real token call remains untested. |
| [Namecheap API](https://www.namecheap.com/support/api/intro/) | Account API with IPv4 allowlist and XML parameters; separate account/access prerequisites. | Product reference, not the first adapter. Avoid coupling the engine to this API. |
| [Spaceship API](https://docs.spaceship.dev/) | Read-scoped availability batch up to 20; its reviewed availability response documents `premiumPricing`, not complete standard registration/renewal prices in that response. | Candidate for another adapter after a full pricing contract review. |
| [Porkbun API](https://porkbun.com/api/json/v3/documentation) | Official docs advertise availability/pricing checks one at a time or 25 per call and a sandbox. | Strong candidate for the next adapter; exact access and response contracts still need validation. |

No partnership or shared credential is assumed. The first adapter is chosen for a precise read-only contract and complete indicative price fields, not for a claim that GoDaddy is universally cheapest or covers every requested TLD.

### Packaging and verification after the first slice

The repository root now has portable Agent Plugins `plugin.json`/`mcp.json`, a DoName skill, and a locked `uv` dependency set. Legacy IsDomainOK source and stale descriptors were removed from this branch. The plugin bundle contains source, UI, manifest, skill and lockfile; the wheel contains the Python engine and UI. The plugin bundle was extracted into a clean directory and ran under Python 3.10; its MCP stdio command completed tool discovery and an offline naming call. An isolated wheel install imported the server and UI. Both manifests passed the published Agent Plugins JSON Schemas. A JavaScript host-bridge smoke test rendered synthetic cards and completed the MCP Apps initialization handshake. These are development tests, not ChatGPT or Claude host validation.

Thirty-three automated tests pass on local Python 3.10 and 3.13. The final synthetic 12-name/24-domain benchmark ran with 24 simulated RDAP calls and one simulated provider batch in 24.72 ms locally, producing 16,917 bytes of JSON. This excludes network and model latency and is not a live performance promise. Codex CLI 0.155.0-alpha.16.4 called `capabilities` through an ephemeral MCP config; Claude Code 2.1.281 called the same tool through a temporary MCP config. Both reported no configured provider. No global MCP config was changed. The available-only option and card filter now hide unavailable optional extensions; text fallback includes both evidence sources, source times and prices. IDE, ChatGPT and visual host rendering remain untested.

### V1 hardening after review of PR #9

2026-09-24 — The CI matrix now checks Python 3.10/3.13 on Linux and Python 3.13 on Windows using the locked dependency set. The Linux packaging lane validates `plugin.json` and `mcp.json` against hash-pinned local copies of the official Agent Plugins 1.0.0 schemas, runs the MCP Apps lifecycle smoke, and builds the wheel and sdist. Linux and Windows 3.13 build the plugin ZIP, extract it into a temporary directory and start the stdio server from its `mcp.json` command; tool discovery, offline calls and UI resource loading are checked without provider credentials or search telemetry. The View now responds to `ui/resource-teardown`, drops listeners/state and reports size changes; its simulated host test verifies teardown acknowledgement and cleanup. Thirty-six Python tests pass locally after adding auth-error and manual-probe privacy checks.

The separate private GoDaddy probe generates disposable synthetic `.com`/`.fr` candidates and uses public `example.com`/`nic.fr` registration controls. It emits redacted status, freshness and price summaries only; it has not been run with a PAT. The 36 Python tests pass locally on 3.10 and 3.13. A private ChatGPT developer-mode tunnel runbook follows current OpenAI documentation; no tunnel, ChatGPT connection or visual host test has been performed. Keep PR #9 in draft until those external checks are done.

### Private live validation

2026-09-24 — The manual GoDaddy probe ran locally with a temporary PAT supplied only through the process environment. It confirmed registered controls and available synthetic candidates under both `.com` and `.fr`, including definitive provider availability, indicative registration prices and renewal prices for the tested terms. There were no observed provider errors or rate limits. The probe's redacted summary reported `live_criteria_met=true`; the token, generated names and raw provider responses were not committed. This proves the tested GoDaddy contract and TLD coverage at that time, not universal coverage or future availability.

An official private Secure MCP Tunnel connected the local stdio server to a ChatGPT developer-mode MCP App. In a real ChatGPT conversation, offline synthetic `screen_names` results rendered DoName cards and the **Available only** filter worked. A keyless live RDAP check returned `registered` for public `.com` and `.fr` controls, and `not_found_in_registration_data` for synthetic RDAP 404 cases with source and check time. A second card View displayed that cautious status and unknown prices. The text/structured fallback remained useful.

A provider-enabled ChatGPT `check_domains` call then returned registered public controls and available synthetic `.com`/`.fr` candidates from GoDaddy, with registration and renewal prices, currency, source time and no reported errors. A real `screen_names` card showed both extensions as provider-available with those indicative prices and renewal details; the candidate passed `match="all"`. This confirms the tested provider-to-ChatGPT path. It does not establish universal TLD coverage, future availability, checkout pricing or public plugin readiness. No private candidates, token or raw provider response entered Git. The private App is not a public plugin or production deployment, and PR #9 remains draft pending final review.

### Release review and publication boundary

2026-09-24 — The user chose GoDaddy as the sole V1 provider and reported that GitHub Actions cannot be the release gate. The local `scripts/release_check.py` checks the lockfile, Python 3.10/3.13 tests, Agent Plugins manifests, MCP Apps lifecycle, extracted plugin startup/tool discovery and Python builds. The plugin builder now has an explicit public-file list; a separate artifact audit rejects unexpected, untracked or secret-shaped files. The current release candidate passes 38 Python tests on each version and the full local gate on Windows. No live provider call is part of that gate.

Review of PR #9 also tightened GoDaddy truth handling: `available=true` is only shown as verified when the response marks it definitive; otherwise prices are withheld and the result remains unconfirmed. Money values use the currency's minor unit rather than assuming two decimals. Cards now label RDAP as the primary source for RDAP statuses and show secondary provider evidence separately. The README and changelog describe tested hosts and release limits. A pattern scan of tracked content and Git diffs found no recognizable PAT, OpenAI key or private-key marker; this cannot prove that every possible secret format is absent.

PR #8 and PR #9 were merged into `main`. The published GitHub release `doname-v0.1.0` contains the source, locally runnable plugin bundle, Python wheel and source distribution with SHA-256 checksums. GitHub secret scanning and push protection are enabled. This is not PyPI publication, a production service, or a public ChatGPT directory listing. A public ChatGPT plugin still requires a stable HTTPS MCP service with authentication, abuse controls, privacy review and OpenAI submission. V2 may add providers after this single-provider path is stable.
