"""
Wiring `on_response` into the generated core.

`ApiClient.call_api` is the one place method, URL, headers and body all exist
alongside the response, so the hook wraps that.
"""

from __future__ import annotations

import json
import logging
import time
from contextvars import ContextVar
from typing import Any, Mapping, Optional

from msgeasy._events import RequestEvent, ResponseHandler
from msgeasy._headers import RateLimit, request_id_of, retry_after_of

logger = logging.getLogger("msgeasy")

#: Which attempt is in flight. The retry loop is in `_transport` and the recording
#: is here, with the generated core in between, so the number is carried out of
#: band rather than threaded through it — a header would reach the server, which
#: is not the SDK's to spend.
attempt_var: ContextVar[int] = ContextVar("msgeasy_attempt", default=1)

_IDEMPOTENCY_KEY = "Idempotency-Key"


def _parse(raw: Any) -> Any:
    """JSON where it is JSON, the raw text where it is not, `None` where empty."""
    if raw is None or raw == b"" or raw == "":
        return None
    if isinstance(raw, (bytes, bytearray)):
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError:
            return "<binary>"
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except ValueError:
            return raw
    return raw


def _request_body(body: Any, post_params: Any) -> Any:
    """A multipart body is the file's bytes; the event carries what it was instead."""
    if body is not None:
        return _parse(body)
    if not post_params:
        return None
    for name, value in post_params:
        if name != "file":
            continue
        # (filename, data, mime_type), as the generated core builds it.
        if isinstance(value, (tuple, list)) and len(value) >= 3:
            filename, data, mime_type = value[0], value[1], value[2]
            return {
                "filename": filename,
                "mimeType": mime_type,
                "sizeBytes": len(data) if data is not None else None,
            }
    return "<form data>"


def _idempotency_key(headers: Optional[Mapping[str, str]]) -> Optional[str]:
    if not headers:
        return None
    for name, value in headers.items():
        if name.lower() == _IDEMPOTENCY_KEY.lower():
            return value
    return None


def install(api_client: Any, on_response: ResponseHandler) -> None:
    """Replaces `call_api` with one that reports every attempt to `on_response`."""
    inner = api_client.call_api

    def observed(
        method: str,
        url: str,
        header_params: Optional[Mapping[str, str]] = None,
        body: Any = None,
        post_params: Any = None,
        _request_timeout: Any = None,
    ) -> Any:
        started = time.perf_counter()
        attempt = attempt_var.get()
        key = _idempotency_key(header_params)

        def emit(**fields: Any) -> None:
            # Never let a caller's own handler break the request it is only watching.
            try:
                on_response(
                    RequestEvent(
                        method=method,
                        url=url,
                        request_body=_request_body(body, post_params),
                        idempotency_key=key,
                        elapsed_ms=int((time.perf_counter() - started) * 1000),
                        attempt=attempt,
                        **fields,
                    )
                )
            except Exception:
                logger.warning("on_response handler raised; ignoring", exc_info=True)

        try:
            response = inner(
                method,
                url,
                header_params=header_params,
                body=body,
                post_params=post_params,
                _request_timeout=_request_timeout,
            )
        except Exception as exc:
            emit(
                status=None,
                response_body=None,
                request_id=None,
                rate_limit=None,
                retry_after_seconds=None,
                transport_error=str(exc) or type(exc).__name__,
            )
            raise

        # Safe to read here: `read()` caches, and the generated core reads it again
        # before deserializing.
        raw = response.read()
        headers = response.headers
        emit(
            status=response.status,
            response_body=_parse(raw),
            request_id=request_id_of(headers),
            rate_limit=RateLimit.of(headers),
            retry_after_seconds=retry_after_of(headers),
            transport_error=None,
        )
        return response

    api_client.call_api = observed
