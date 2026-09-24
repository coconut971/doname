# Changelog

## DoName 0.1.0 — 2026-09-24

- Rebuilt the former IsDomainOK project as a local MCP plugin for AI naming research, while retaining MIT licensing and repository history.
- Added bounded batch checks, multi-extension name screening, provider-neutral evidence, keyless RDAP, and optional DNS observations. DNS NXDOMAIN and RDAP 404 never imply purchase availability.
- Added a read-only GoDaddy Domains v3 adapter for definitive availability and indicative registration and renewal prices when a user supplies a PAT locally. Non-definitive replies stay unverified.
- Added MCP Apps cards with a complete structured/text fallback, portable Agent Plugins manifests and skill, stdio and loopback HTTP transports.
- Validated a private GoDaddy `.com`/`.fr` probe and a real ChatGPT developer-mode tunnel conversation with synthetic names. No public ChatGPT service is included.
- Added a credential-free local release gate for Python 3.10/3.13 tests, manifest and UI checks, bundle startup, Python builds and artifact audit. Public GitHub Actions are not required for release.

This release is non-transactional. Prices and availability are provider and time specific, not checkout guarantees. The previous `v1.0.0` tag belongs to IsDomainOK; DoName tags begin with `doname-v`.
