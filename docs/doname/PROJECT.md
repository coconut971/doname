# DoName — project memory and refoundation brief

Date: 2026-09-24. Status: product direction and implementation proposal; not an implemented release.

Repository inspected: `coconut971/isdomainok`, public. Baseline: `main` at `80fea7d9a8cb13fc1509286d7c254c47041ba4b1` (IsDomainOK 2.1.0). Keep this history. **DoName V1** names the new product milestone; do not silently downgrade an already published package's version.

## 1. Explicit user decisions

The name is **DoName**, spelled D-O-N-A-M-E. Rebuild the current project around an installable AI experience for ChatGPT, Codex, Claude and other compatible hosts, rather than a DNS command-line utility. The user wants a finished, fast, clear and simple product, not unnecessary size. Source must be public; searches and operational data must remain private.

**V1 is non-transactional, not disconnected from the market.** It should already be able to use at least one real read-only availability/pricing source so an AI can obtain current registrability and price information instead of guessing. It may show the provider, registration price, renewal price when available, freshness, unsupported TLDs and an outbound link to a registrar or broker. DoName itself must not charge, receive a commission, register a domain, run checkout, mutate DNS or silently act on behalf of the user in V1. Commercial relationships, affiliate economics, reseller/registrar actions and in-chat purchasing belong to a later explicitly approved phase.

Design DoName around a small provider abstraction from the start so the engine is not permanently coupled to GoDaddy, Namecheap or another single registrar. Codex should investigate current registrar/registry/reseller APIs and choose a viable first V1 provider based on access, coverage, data quality, terms, pricing fields and maintainability; do not assume a partnership exists.

Existing principles to preserve: MIT license, useful local/self-hosted execution, a keyless evidence mode, no telemetry by default, no automatic domain purchase, and no mandatory model API. A public ChatGPT plugin may require a DoName-operated remote MCP service and server-side provider credentials; that hosted path must be cleanly separated from local/self-hosted use and must not make local use depend on the hosted service.

## 2. Architecture decision proposed for implementation

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
