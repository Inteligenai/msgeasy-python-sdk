"""
Every exception this SDK raises, and the one function that builds them.

Read from the response body, not the generated `ApiError` model, whose enum
would reject a code added after this release.

Branch on `code`. The classes group codes by what you can do about them, so
`except QuotaError` is a shortcut — never a replacement for the code itself,
which is the only thing that survives a new code being added.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Union

from msgeasy._headers import Headers, RateLimit, request_id_of, retry_after_of


class MsgEasyError(Exception):
    """Base for everything this SDK raises."""

    #: Set from a refusal's headers; never on a connection fault, which has none.
    rate_limit: Optional[RateLimit] = None


class ValidationError(MsgEasyError, ValueError):
    """
    Refused here, before anything was sent. The request is wrong, not the answer.

    Also a `ValueError`, which is what a Python caller expects from a bad argument
    — so it is catchable either way.
    """


class APIConnectionError(MsgEasyError):
    """No response at all — DNS, a reset connection, or a timeout."""


class BadEnvelopeError(MsgEasyError):
    """
    A non-2xx whose body was not our error envelope — almost always something
    other than the API answering, such as a proxy's HTML page.

    Deliberately not an `APIError` and deliberately carrying no `code`: a caller
    branching on `code` must never be handed an absence where a code belongs.
    """

    def __init__(
        self,
        status: int,
        body: Optional[str],
        request_id: Optional[str] = None,
        rate_limit: Optional[RateLimit] = None,
    ) -> None:
        super().__init__(f"The API returned {status} without a recognisable error body.")
        self.status = status
        self.body = body
        self.request_id = request_id
        self.rate_limit = rate_limit


class APIError(MsgEasyError):
    """
    A refusal carrying the `/v1` error envelope, and where an unrecognised
    `code` lands so an older SDK still surfaces a newer refusal.
    """

    def __init__(
        self,
        message: str,
        *,
        status: int,
        code: Optional[str],
        details: Any = None,
        request_id: Optional[str] = None,
        retry_after_seconds: Optional[int] = None,
        rate_limit: Optional[RateLimit] = None,
        body: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.details = details
        self.request_id = request_id
        self.retry_after_seconds = retry_after_seconds
        self.rate_limit = rate_limit
        self.body = body


class AuthenticationError(APIError):
    """The key is missing, malformed, expired or revoked."""


class PermissionDeniedError(APIError):
    """The key is valid but its scopes do not cover this route."""


class RateLimitError(APIError):
    """Too many requests for this key. `retry_after_seconds` says how long to wait."""


class QuotaError(APIError):
    """
    An allowance is spent and nothing refills until the cycle turns. `code`
    says which — the plan's, the key's own, or its spend cap.
    """


class SetupRequiredError(APIError):
    """
    The account is not ready: no Verify template, no sender, or no live
    WhatsApp connection. Fixed in the console, not in the request.
    """


class NotFoundError(APIError):
    """No such resource, or it belongs to another account — deliberately
    indistinguishable."""


class InvalidRequestError(APIError):
    """The request itself is wrong; `message` says how."""


class IdempotencyError(APIError):
    """
    An `Idempotency-Key` named two operations, or its first request is still
    in flight. Only the second carries `retry_after_seconds`.
    """


class WindowExpiredError(APIError):
    """Outside WhatsApp's 24-hour window — send a template instead."""


class TemplateError(APIError):
    """The template will not serve this send or this edit; `code` says why."""


class MetaError(APIError):
    """Meta failed the operation; `details` carries their code and trace id."""


class ServiceUnavailableError(APIError):
    """A dependency was briefly unreachable, so the operation did not run."""


class TestKeyError(APIError):
    """A `test` key attempted a write that would permanently spend something at
    Meta."""


# A remedy hint, not a catalogue: an unlisted code degrades to `APIError`, which
# is what lets the API add codes without a release here.
#
# **Identical to the TypeScript SDK's `CODE_ERRORS`** — one entry out of step is a
# divergence nothing would catch, so change both together.
_CODE_ERRORS = {
    "invalid_api_key": AuthenticationError,
    "insufficient_scope": PermissionDeniedError,
    "rate_limited": RateLimitError,
    "quota_exceeded": QuotaError,
    "key_limit_reached": QuotaError,
    "spend_cap_reached": QuotaError,
    "verify_not_configured": SetupRequiredError,
    "no_sender": SetupRequiredError,
    "whatsapp_not_connected": SetupRequiredError,
    "not_found": NotFoundError,
    "invalid_request": InvalidRequestError,
    "unsupported_media_type": InvalidRequestError,
    "media_too_large": InvalidRequestError,
    "idempotency_conflict": IdempotencyError,
    "window_expired": WindowExpiredError,
    "template_not_approved": TemplateError,
    "template_name_taken": TemplateError,
    "template_not_editable": TemplateError,
    "template_category_not_allowed": TemplateError,
    "meta_error": MetaError,
    "service_unavailable": ServiceUnavailableError,
    "test_key_not_allowed": TestKeyError,
}


def error_from_response(
    status: int, headers: Headers, body: Optional[str]
) -> Union[APIError, BadEnvelopeError]:
    """Builds the exception for a refusal, whatever shape the body turned out to be."""
    envelope = _envelope(body)
    code = envelope.get("code")

    # No `code` means this was not our envelope, so it is not a refusal we can
    # describe — a different fact, and a different class.
    if not isinstance(code, str):
        return BadEnvelopeError(
            status=status,
            body=body,
            request_id=request_id_of(headers),
            rate_limit=RateLimit.of(headers),
        )

    error_class = _CODE_ERRORS.get(code, APIError)
    return error_class(
        envelope.get("message") or f"HTTP {status}",
        status=status,
        code=code,
        details=envelope.get("details"),
        request_id=request_id_of(headers),
        retry_after_seconds=retry_after_of(headers),
        rate_limit=RateLimit.of(headers),
        body=body,
    )


def _envelope(body: Optional[str]) -> Dict[str, Any]:
    """A proxy's HTML error page, or a truncated body, still has to raise
    cleanly."""
    try:
        parsed = json.loads(body or "")
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}
