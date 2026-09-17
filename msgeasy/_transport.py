"""The one place a request is made, retried and turned into an exception."""

from __future__ import annotations

import asyncio
import sys
import time
import uuid
import warnings
from types import FrameType
from typing import Any, Callable, Dict, Optional, TypeVar

import urllib3

from msgeasy._generated.api_response import ApiResponse
from msgeasy._generated.exceptions import ApiException
from msgeasy._headers import RateLimit
from msgeasy._observe import attempt_var
from msgeasy._policy import wait_before_retry
from msgeasy.errors import (
    APIConnectionError,
    MsgEasyError,
    ValidationError,
    error_from_response,
)

IDEMPOTENCY_KEY = "Idempotency-Key"

#: The API's own cap. Refused here so a typo costs no round trip.
MAX_IDEMPOTENCY_KEY_LENGTH = 255

T = TypeVar("T")

#: One attempt: given the headers to send and the timeout, produce a response.
Attempt = Callable[[Dict[str, Any], float], ApiResponse[T]]

#: The opening words are a documented filter key — README's "Async frameworks" tells
#: callers to silence this with `message="This client is synchronous"`, so rewording the
#: start of it breaks their filter.
BLOCKING_WARNING = (
    "This client is synchronous, so the call blocks the event loop until it returns "
    "and every other request on this worker waits with it. Declare the route `def` "
    "instead of `async def` and the framework will run it on a thread, or call it "
    "through `asyncio.to_thread` / Starlette's `run_in_threadpool`."
)


def _caller_stacklevel() -> int:
    """
    How far `warnings.warn` has to climb out of this package to reach the caller's
    own line.

    Walked rather than hard-coded, because the distance differs by method: most
    reach `call_raw` through `call` and the resource method, while `templates.list`
    adds `_page`, and `list_all` adds `_page`, a lambda and `paginate`. A fixed
    count lands inside this package on the longer paths, and that is worse than a
    wrong filename — the default filter registers a warning against the line it was
    attributed to, so blaming our own line once silences every other blocking call
    site in the process for its lifetime.

    `skip_file_prefixes` states this declaratively, but it needs 3.12 and this
    package targets 3.10.
    """
    package = __name__.split(".")[0]
    # `stacklevel=1` is this function's caller, `_warn_if_on_event_loop`, so the
    # walk starts at that frame and each frame further out is one level more.
    frame: Optional[FrameType] = sys._getframe(1)
    level = 1
    while frame is not None and frame.f_globals.get("__name__", "").split(".")[0] == package:
        frame = frame.f_back
        level += 1
    return level


def _warn_if_on_event_loop() -> None:
    """
    Fires only when a call would actually block a loop, which is what makes it safe
    to warn unconditionally: `get_running_loop` succeeds on the loop thread alone, so
    a `def` route, `run_in_threadpool`, Flask, Django and a plain script all raise
    here and warn nothing.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return
    warnings.warn(BLOCKING_WARNING, RuntimeWarning, stacklevel=_caller_stacklevel())


class Transport:
    def __init__(self, api_client: Any, timeout: float) -> None:
        # `Any`: the generated client carries no annotations, so this is the
        # boundary where types stop and callers cast on the way back.
        self.api_client = api_client
        self._timeout = timeout
        self.rate_limit: Optional[RateLimit] = None
        """What the most recent response reported, so a caller can pace itself."""

    def call(
        self,
        operation: Callable[..., ApiResponse[T]],
        *,
        idempotent: bool,
        timeout: Optional[float] = None,
        idempotency_key: Optional[str] = None,
        **kwargs: Any,
    ) -> T:
        """Runs a generated operation. See `call_raw` for `idempotent`."""
        return self.call_raw(
            lambda headers, request_timeout: operation(
                _headers=headers, _request_timeout=request_timeout, **kwargs
            ),
            idempotent=idempotent,
            timeout=timeout,
            idempotency_key=idempotency_key,
        )

    def call_raw(
        self,
        attempt: "Attempt[T]",
        *,
        idempotent: bool,
        timeout: Optional[float] = None,
        idempotency_key: Optional[str] = None,
    ) -> T:
        """
        The retry loop. `idempotent` says whether the API can replay this call, and
        so whether an `Idempotency-Key` is worth sending.
        """
        _warn_if_on_event_loop()

        if idempotency_key is not None:
            # Refused rather than replaced. An empty string is almost always an unset
            # variable, and minting one instead would leave the caller believing they
            # hold a key they can replay.
            if not idempotency_key:
                raise ValidationError("idempotency_key must not be empty.")
            if len(idempotency_key) > MAX_IDEMPOTENCY_KEY_LENGTH:
                raise ValidationError(
                    f"idempotency_key must be {MAX_IDEMPOTENCY_KEY_LENGTH} characters or fewer, "
                    f"got {len(idempotency_key)}."
                )

        # Reused across attempts: a fresh key per retry would let a write that
        # already landed run again. A caller's own key is kept, so they can replay
        # this exact call later.
        headers = {IDEMPOTENCY_KEY: idempotency_key or uuid.uuid4().hex} if idempotent else {}
        request_timeout = float(self._timeout if timeout is None else timeout)

        made = 0
        while True:
            made += 1
            token = attempt_var.set(made)
            try:
                # A copy per attempt: serialising a request adds the client's own
                # default headers to the dict it is handed.
                response = attempt(dict(headers), request_timeout)
            except ApiException as exc:
                error = _as_error(exc)
            except urllib3.exceptions.HTTPError as exc:
                # Never completed: timeouts, DNS, a reset connection. Only the
                # SSL failure arrives above, converted by the generated core.
                error = APIConnectionError(str(exc) or type(exc).__name__)
            else:
                self.rate_limit = RateLimit.of(response.headers)
                return response.data
            finally:
                attempt_var.reset(token)

            # After a `429` this is the reading a caller most wants.
            self.rate_limit = error.rate_limit or self.rate_limit

            wait = wait_before_retry(error, made)
            if wait is None:
                raise error
            time.sleep(wait)


def _as_error(exc: ApiException) -> MsgEasyError:
    # A failed TLS handshake arrives status-less; nothing was served, so it is a
    # connection fault rather than a refusal.
    if not exc.status:
        return APIConnectionError(exc.reason or "Request failed")

    return error_from_response(exc.status, exc.headers, exc.body)
