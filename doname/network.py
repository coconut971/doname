"""Bounded HTTPS JSON reads with redirects and environment proxies disabled."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = build_opener(ProxyHandler({}), NoRedirect())


class NetworkError(Exception):
    def __init__(self, code: str, retry_after_seconds: int | None = None):
        super().__init__(code)
        self.code = code
        self.retry_after_seconds = retry_after_seconds


def request_json(url: str, *, method: str = "GET", payload: dict | None = None,
                 headers: dict[str, str] | None = None, timeout: float = 3.0, max_bytes: int = 1_000_000) -> dict:
    if not url.startswith("https://") or timeout <= 0:
        raise NetworkError("invalid_request")
    if method not in {"GET", "POST"} or (method == "GET" and payload is not None):
        raise NetworkError("invalid_request")
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8") if payload is not None else None
    if body is not None and len(body) > 4096:
        raise NetworkError("request_too_large")
    request = Request(url, data=body, method=method,
                      headers={"Accept": "application/json, application/rdap+json", "Content-Type": "application/json",
                               "User-Agent": "DoName/0.1", **(headers or {})})
    try:
        with _OPENER.open(request, timeout=timeout) as response:
            body = response.read(max_bytes + 1)
    except HTTPError as exc:
        retry = exc.headers.get("Retry-After") if exc.headers else None
        retry_seconds = min(int(retry), 3600) if retry and retry.isdigit() else None
        raise NetworkError(f"http_{exc.code}", retry_seconds) from None
    except (URLError, TimeoutError, OSError) as exc:
        code = "timeout" if isinstance(exc, TimeoutError) or "timed out" in str(exc).lower() else "network_error"
        raise NetworkError(code) from None
    if len(body) > max_bytes:
        raise NetworkError("response_too_large")
    try:
        data = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise NetworkError("invalid_json") from None
    if not isinstance(data, dict):
        raise NetworkError("invalid_json_shape")
    return data


def get_json(url: str, **kwargs) -> dict:
    return request_json(url, **kwargs)


def post_json(url: str, payload: dict, **kwargs) -> dict:
    return request_json(url, method="POST", payload=payload, **kwargs)
