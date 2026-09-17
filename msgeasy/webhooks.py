"""
Verifying a webhook we delivered. A port of `lib/webhooks/signature.ts`;
the two must agree byte-for-byte or every delivery is rejected.
"""

from __future__ import annotations

import hashlib
import hmac
from base64 import b64encode
from dataclasses import dataclass
from time import time
from typing import Any, Mapping, Optional, Union

#: The header carrying the signature.
#:
#: Lower-case because that is the one spelling every receiver can look up: Node
#: lower-cases inbound header names, and Python's frameworks are case-insensitive,
#: so lower-case works everywhere while the canonical casing does not. The sender
#: keeps its own copy and is unaffected.
SIGNATURE_HEADER = "x-msgeasy-signature"

#: How far apart the clocks may be. The timestamp is inside the signed payload,
#: so this is what stops a captured delivery being replayed for ever.
DEFAULT_TOLERANCE_SECONDS = 300

Body = Union[str, bytes]

#: Whatever a framework calls a header bag, plus the bare value.
SignatureHeaders = Union[str, Mapping[str, Any], None]


@dataclass(frozen=True)
class SignatureResult:
    """
    Why a delivery was refused. A bare `False` cannot be logged or acted on, and
    "stale clock" and "wrong secret" need different answers.

    Truthy when `ok`, so `if verify_webhook_signature(...):` still reads naturally.
    """

    ok: bool
    #: One of: no_secret_configured, missing_header, malformed_header,
    #: stale_timestamp, bad_signature. `None` when `ok`.
    reason: Optional[str] = None

    def __bool__(self) -> bool:
        return self.ok


_OK = SignatureResult(ok=True)


class _Duplicate:
    """Stands in for a header that arrived more than once, so the refusal is
    reported as malformed rather than raising inside the caller's handler."""


_DUPLICATE = _Duplicate()


def _header_value(headers: SignatureHeaders) -> Union[str, "_Duplicate", None]:
    """
    Pulls the signature out of whatever the caller passed.

    Done here rather than by the caller because the lookup is where this goes
    wrong, and getting it wrong fails silently as an unsigned delivery.

    A non-string value means the header arrived more than once, which some
    frameworks hand over as a list. Two signatures is not one delivery to trust,
    so it comes back as `_DUPLICATE` rather than being indexed into.
    """
    if headers is None or isinstance(headers, str):
        return headers
    for name, value in headers.items():
        if name.lower() == SIGNATURE_HEADER:
            return value if isinstance(value, str) else _DUPLICATE
    return None


def verify_webhook_signature(
    body: Body,
    headers: SignatureHeaders,
    secret: str,
    *,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
    now: Optional[float] = None,
) -> SignatureResult:
    """
    Whether this delivery is ours, unmodified and recent. `body` must be the
    raw bytes — a re-serialized body will not match.

    Pass the whole header bag; the lookup is case-insensitive and done here.
    """
    if not secret:
        return SignatureResult(ok=False, reason="no_secret_configured")

    header = _header_value(headers)
    if isinstance(header, _Duplicate):
        return SignatureResult(ok=False, reason="malformed_header")
    if not header:
        return SignatureResult(ok=False, reason="missing_header")

    timestamp, received = _parse(header)
    if timestamp is None or received is None:
        return SignatureResult(ok=False, reason="malformed_header")

    seconds = int(time() if now is None else now)
    if abs(seconds - timestamp) > tolerance_seconds:
        return SignatureResult(ok=False, reason="stale_timestamp")

    if not hmac.compare_digest(_sign(body, timestamp, secret), received):
        return SignatureResult(ok=False, reason="bad_signature")

    return _OK


def _parse(header: Optional[str]) -> "tuple[Optional[int], Optional[str]]":
    """Reads `t=<unix>,v1=<base64>`, tolerating any order and extra fields."""
    if not header:
        return None, None

    fields = {}
    seen_v1 = 0
    for piece in header.split(","):
        key, separator, value = piece.strip().partition("=")
        # Counted before the separator check, so a valueless `v1` still counts as a
        # second signature rather than being skipped — the TypeScript side splits
        # on `=` and keeps the key either way.
        if key == "v1":
            seen_v1 += 1
        # Base64 carries its own `=` padding, so only the first one separates.
        if separator:
            fields[key] = value

    # Two deliveries joined into one header arrive comma-joined, and the dict above
    # would keep the last pair — so a bogus signature followed by a valid one would
    # pass.
    if seen_v1 != 1:
        return None, None

    try:
        return int(fields["t"]), fields["v1"]
    except (KeyError, ValueError):
        return None, None


def _sign(body: Body, timestamp: int, secret: str) -> str:
    payload = body if isinstance(body, bytes) else body.encode("utf-8")
    signed = str(timestamp).encode("ascii") + b"." + payload
    return b64encode(hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).digest()).decode(
        "ascii"
    )
