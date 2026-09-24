---
name: doname-naming
description: Help users find project, product or company names whose requested domains have honestly checked registration and provider evidence. Use when the user asks for names with domain availability, mandatory extensions or a registration budget.
license: MIT
compatibility: Requires the DoName MCP server. Provider availability and pricing require a configured read-only provider credential; the keyless path uses RDAP.
---

# DoName naming workflow

You invent and judge names. DoName checks domain evidence. Keep those roles separate.

1. Read the brief for purpose, language, tone, length, forbidden terms, extensions, mandatory extensions and budget. Do not pass the natural-language brief to DoName or any provider.
2. Generate a small varied pool of base names. Deduplicate and remove obvious brief mismatches yourself. Pass at most 12 names per `screen_names` call; use at most two bounded rounds before presenting a shortlist.
3. Call `capabilities` if the provider state is unknown. Call `screen_names` with the exact extension logic: `match="all"` for `.com ET .fr`, `match="any"` for at least one, and `required_extensions=["com"]` for mandatory `.com`. Supply a three-letter currency with any budget. Use `available_only=true` when the user wants only verified available names.
4. Read each grouped result. `available_at_provider` means the named provider offered registration at the shown time, subject to change. `registered` means a validated RDAP domain object. `unavailable_at_provider` is a refusal from that provider, not a registration claim. `not_found_in_registration_data`, DNS NXDOMAIN, timeout, unsupported coverage and provider errors never mean available.
5. Recommend a short selection, usually 3–6 names, with the reasons they fit the brief, required domain statuses, provider, checked time, registration price and renewal price when supplied. If no provider is configured, present promising names as **unverified for purchase**. Do not promote an unknown price as within budget.
6. Keep creative preference subjective. Do not assign invented probability or brand scores. Do not claim trademark or company-name clearance. Do not purchase, reserve or register a domain.

The MCP tool result is complete without the optional cards UI. External sources see the queried domains; the AI host sees the conversation. DoName does not store a search history or send telemetry by default.
