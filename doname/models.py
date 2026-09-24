"""Evidence types keep registration, registrability and DNS separate."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class Evidence:
    status: str
    source: str
    checked_at: str = field(default_factory=now)
    reason: str | None = None
    retry_after_seconds: int | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["age_seconds"] = max(0, int((datetime.now(timezone.utc) - datetime.fromisoformat(self.checked_at.replace("Z", "+00:00"))).total_seconds()))
        return result


@dataclass
class Price:
    amount: str
    currency: str
    period_years: int
    kind: str
    provider: str
    checked_at: str
    indicative: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DomainResult:
    domain: str
    status: str
    reason: str
    registration: Evidence | None = None
    registrability: Evidence | None = None
    dns: Evidence | None = None
    registration_price: Price | None = None
    renewal_price: Price | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "status": self.status,
            "reason": self.reason,
            "registration": self.registration.to_dict() if self.registration else None,
            "registrability": self.registrability.to_dict() if self.registrability else None,
            "dns": self.dns.to_dict() if self.dns else None,
            "registration_price": self.registration_price.to_dict() if self.registration_price else None,
            "renewal_price": self.renewal_price.to_dict() if self.renewal_price else None,
        }
