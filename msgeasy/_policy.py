"""
The retry and timeout policy, pinned by `docs/sdk/sdk-conformance.md` §4.
Shared with the TypeScript SDK — changing one number in isolation breaks that.
"""

from __future__ import annotations

import random
from typing import Optional

from msgeasy.errors import APIConnectionError, APIError, BadEnvelopeError, MsgEasyError

DEFAULT_TIMEOUT_SECONDS = 30.0

#: The wait after attempt 1, then after attempt 2. `Retry-After` overrides both.
BACKOFF_SECONDS = (0.5, 1.0)

#: The original request plus one retry per wait above. Derived so the two cannot
#: fall out of step and leave `_backoff` indexing past the end.
ATTEMPTS = len(BACKOFF_SECONDS) + 1

#: So a fleet of clients refused together does not come back in lockstep.
JITTER_RATIO = 0.25

_RETRYABLE_CODES = frozenset({"rate_limited", "service_unavailable"})

_IDEMPOTENCY_CONFLICT = "idempotency_conflict"


def wait_before_retry(error: MsgEasyError, attempt: int) -> Optional[float]:
    """
    Seconds to wait before the next attempt, or `None` to give up and raise.
    `attempt` counts attempts already made.
    """
    if attempt >= ATTEMPTS:
        return None

    # Nothing was received, so the operation may not have run — and the retry
    # reuses the idempotency key, so one that did land replays.
    if isinstance(error, APIConnectionError):
        return _backoff(attempt)

    # Something that was not the API answered, so waiting changes nothing. Stated
    # rather than left to fall through the `APIError` check below.
    if isinstance(error, BadEnvelopeError):
        return None

    if not isinstance(error, APIError):
        return None

    # `is not None` rather than truthiness: `Retry-After: 0` means retry now, and
    # testing truthiness would drop it and fall back to the backoff instead.
    if error.code in _RETRYABLE_CODES:
        if error.retry_after_seconds is not None:
            return float(error.retry_after_seconds)
        return _backoff(attempt)

    # Only the still-in-flight case carries `Retry-After`; a key reused for a
    # different body never will.
    if error.code == _IDEMPOTENCY_CONFLICT and error.retry_after_seconds is not None:
        return float(error.retry_after_seconds)

    # `meta_error` included: a `5xx` releases the stored key, so a retried write
    # could send twice.
    return None


def _backoff(attempt: int) -> float:
    return BACKOFF_SECONDS[attempt - 1] * (1 + random.random() * JITTER_RATIO)
