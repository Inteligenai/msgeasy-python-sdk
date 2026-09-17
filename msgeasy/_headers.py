"""Response-header reads, shared by `_transport` and `errors`."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

REQUEST_ID = "X-Request-Id"
RETRY_AFTER = "Retry-After"

Headers = Optional[Mapping[str, str]]


@dataclass(frozen=True)
class RateLimit:
    """
    What is left of the key's per-minute allowance. `None` means unknown —
    the limiter never charged this response — not nothing left.
    """

    limit: int
    remaining: int
    reset_seconds: int

    @classmethod
    def of(cls, headers: Headers) -> Optional["RateLimit"]:
        limit = _int(headers, "X-RateLimit-Limit")
        remaining = _int(headers, "X-RateLimit-Remaining")
        reset_seconds = _int(headers, "X-RateLimit-Reset")

        if limit is None or remaining is None or reset_seconds is None:
            return None
        return cls(limit=limit, remaining=remaining, reset_seconds=reset_seconds)


def request_id_of(headers: Headers) -> Optional[str]:
    """The id to quote in a support ticket; the key into the console's request log."""
    return headers.get(REQUEST_ID) if headers else None


def retry_after_of(headers: Headers) -> Optional[int]:
    """
    Whole seconds, the only form `/v1` sends; anything else reads as absent.

    `0` is kept: it means retry now, and for `idempotency_conflict` the presence of
    the header is what separates "still in flight" from "wrong body".
    """
    seconds = _int(headers, RETRY_AFTER)
    return seconds if seconds is not None and seconds >= 0 else None


def _int(headers: Headers, name: str) -> Optional[int]:
    raw = headers.get(name) if headers else None
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None
