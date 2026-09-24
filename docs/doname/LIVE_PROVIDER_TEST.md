# Private GoDaddy V1 verification

This is a manual live test, separate from public CI. Run it only in a local environment with a read-scoped `GODADDY_PAT` supplied by a secret manager. Do not put the token in a command argument, prompt, file, screenshot or GitHub secret for this public PR. Do not save the output in Git or CI artifacts.

```powershell
uv sync --locked
uv run --locked python scripts/live_godaddy_probe.py
```

The script refuses to run without `GODADDY_PAT`. It makes one read-only provider batch for four domains: the public registered `example.com` and `nic.fr`, plus random synthetic names under `.com` and `.fr`. RDAP also checks those four domains. The random labels are generated in memory; output uses case labels and extension only. The registrar and RDAP services can still observe queried domains. DoName stores no search history.

Read the four case rows and the final `live_criteria_met` line. Inspect provider status, `definitive`, source and check time, registration price, and renewal price if supplied. `available_at_provider` means GoDaddy offered registration then; it is still indicative until a later transaction, which this V1 never performs. A `.fr` refusal or unsupported result is a measured coverage limit, not a claim that the domain is registered. If a random candidate is unexpectedly unavailable, rerun once; each run generates a new random label. The script exits 2 when both registered examples are not confirmed by RDAP or both generated domains are not available with a registration price.

Provider `error`, `timeout`, `rate_limited`, and `retry_after_seconds` appear in the summary if encountered naturally. Do not deliberately exhaust the provider quota. Automated tests inject HTTP 401, HTTP 429 with Retry-After, timeout and malformed payloads without making live provider requests. A renewal price may be absent; record that absence as a limit, not zero. GoDaddy's v3 `renewalPrice` may reflect an API auto-renewal rate rather than a manual renewal rate.

After the run, report the outcome in words: which extension was covered, whether an available result and prices were observed, and whether there were errors. Keep generated domain labels, raw responses, token and account data out of the PR.
