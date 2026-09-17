"""What `on_response` is handed, once per attempt."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from msgeasy._headers import RateLimit


@dataclass(frozen=True)
class RequestEvent:
    """
    One attempt, as it happened on the wire — the only way to see what was sent and
    received, since the methods return the parsed body and nothing else.
    """

    method: str
    #: The full URL, `/v1` included.
    url: str
    #: `None` when no response arrived at all — see `transport_error`.
    status: Optional[int]
    #: Parsed JSON, or a summary of the file for a multipart upload.
    request_body: Any
    #: Parsed JSON, or the raw text when it would not parse.
    response_body: Any
    request_id: Optional[str]
    #: The key actually sent. `None` on reads, which send none.
    idempotency_key: Optional[str]
    rate_limit: Optional[RateLimit]
    retry_after_seconds: Optional[int]
    elapsed_ms: int
    #: 1-based, so a retry is visible as a second event.
    attempt: int
    #: Why nothing came back, when nothing did.
    transport_error: Optional[str]


#: Called once per attempt. Anything it raises is swallowed.
ResponseHandler = Callable[[RequestEvent], None]
