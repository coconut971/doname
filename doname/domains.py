"""Strict registrable-domain and candidate validation, with an offline PSL snapshot."""

from __future__ import annotations

import ipaddress
import re
import unicodedata
from functools import lru_cache

import idna
import tldextract

MAX_NAMES = 12
MAX_TLDS = 5
MAX_DOMAINS = 25
DEFAULT_TLDS = ("com", "fr", "ai", "io", "app")
_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


class InputError(ValueError):
    pass


@lru_cache(maxsize=1)
def _extractor():
    # A bundled public suffix list: no hidden HTTP fetch for validation.
    return tldextract.TLDExtract(cache_dir=None, suffix_list_urls=(), include_psl_private_domains=False)


def _ascii(value: str) -> str:
    if not isinstance(value, str):
        raise InputError("A domain or name must be text.")
    value = value.strip().rstrip(".").lower()
    if not value or len(value) > 253:
        raise InputError("A domain or name must contain 1 to 253 characters.")
    if any(unicodedata.category(char) in {"Cf", "Cc", "Cs"} for char in value):
        raise InputError("Invisible or control characters are not allowed.")
    if any(char in value for char in "/\\:@?#%") or " " in value:
        raise InputError("Use a domain or base name, not a URL, port or path.")
    try:
        ipaddress.ip_address(value)
    except ValueError:
        pass
    else:
        raise InputError("IP addresses are not domain names.")
    try:
        ascii_value = idna.encode(value, uts46=True, std3_rules=True).decode("ascii").lower()
    except idna.IDNAError as exc:
        raise InputError("Invalid IDNA domain or name.") from exc
    if any(not _LABEL.fullmatch(label) for label in ascii_value.split(".")):
        raise InputError("Invalid domain label.")
    return ascii_value


def exact_domain(value: str) -> str:
    domain = _ascii(value)
    parsed = _extractor()(domain)
    if not parsed.suffix or not parsed.domain:
        raise InputError("A known public suffix and registrable label are required.")
    if parsed.subdomain:
        raise InputError("Subdomains are not checked; provide the registrable domain.")
    if domain != f"{parsed.domain}.{parsed.suffix}":
        raise InputError("Provide one registrable domain.")
    return domain


def base_name(value: str) -> str:
    name = _ascii(value)
    if "." in name:
        raise InputError("Candidate names must be a single label; use check_domains for exact domains.")
    return name


def tlds(values: list[str] | None) -> list[str]:
    requested = values if values is not None else list(DEFAULT_TLDS)
    if not isinstance(requested, list) or not 1 <= len(requested) <= MAX_TLDS:
        raise InputError(f"Choose 1 to {MAX_TLDS} extensions.")
    result = []
    for raw in requested:
        suffix = _ascii(raw.lstrip(".") if isinstance(raw, str) else raw)
        probe = _extractor()(f"example.{suffix}")
        if probe.suffix != suffix or probe.domain != "example" or probe.subdomain:
            raise InputError(f"Unsupported public suffix: {raw!r}.")
        if suffix not in result:
            result.append(suffix)
    return result


def exact_batch(values: list[str]) -> list[str]:
    if not isinstance(values, list) or not 1 <= len(values) <= MAX_DOMAINS:
        raise InputError(f"Provide 1 to {MAX_DOMAINS} exact domains.")
    return list(dict.fromkeys(exact_domain(value) for value in values))


def candidate_batch(values: list[str], suffixes: list[str]) -> list[tuple[str, list[str]]]:
    if not isinstance(values, list) or not 1 <= len(values) <= MAX_NAMES:
        raise InputError(f"Provide 1 to {MAX_NAMES} candidate names.")
    names = list(dict.fromkeys(base_name(value) for value in values))
    if len(names) * len(suffixes) > MAX_DOMAINS:
        raise InputError(f"At most {MAX_DOMAINS} expanded domains per call.")
    return [(name, [exact_domain(f"{name}.{suffix}") for suffix in suffixes]) for name in names]
