"""
The checklist in `docs/sdk/sdk-conformance.md` §12, one test per scenario.

The TypeScript SDK runs the same list. These are the only thing that keeps two
hand-written ergonomic layers behaving alike, so a scenario changed here has to
change there too.
"""

from __future__ import annotations

import asyncio
import socket
import threading
import time
import unittest
import warnings
from types import FunctionType
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import ValidationError

from msgeasy import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    BadEnvelopeError,
    IdempotencyError,
    InvalidRequestError,
    MediaHeader,
    Message,
    MetaError,
    MsgEasy,
    MsgEasyError,
    NotFoundError,
    PermissionDeniedError,
    QuotaError,
    RateLimitError,
    RequestEvent,
    ServiceUnavailableError,
    SetupRequiredError,
    TemplateError,
    TestKeyError,
    TextHeader,
    WindowExpiredError,
)
from msgeasy import ValidationError as MsgEasyValidationError
from msgeasy._policy import ATTEMPTS
from msgeasy._transport import IDEMPOTENCY_KEY
from tests.stub import StubServer

MEDIA: Dict[str, Any] = {
    "id": "med_1",
    "filename": "hello.txt",
    "mimeType": "text/plain",
    "sizeBytes": 5,
    "createdAt": "2026-09-07T10:00:00.000Z",
}

MESSAGE: Dict[str, Any] = {
    "id": "msg_1",
    "status": "accepted",
    "to": "+919876543210",
    "type": "text",
    "whatsappMessageId": None,
    "error": None,
    "createdAt": "2026-09-07T10:00:00.000Z",
}


def closed_port_url() -> str:
    """A port nothing is listening on, so a connection is refused rather than
    left to time out."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return f"http://127.0.0.1:{probe.getsockname()[1]}"


def template(id: str, header: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "id": id,
        "name": "order_update",
        "status": "approved",
        "category": "UTILITY",
        "language": "en",
        "body": "Hi",
        "variables": [],
        "header": header,
        "footer": None,
        "rejectionReason": None,
        "approvedAt": None,
        "createdAt": "2026-09-07T10:00:00.000Z",
        "updatedAt": "2026-09-07T10:00:00.000Z",
    }


class ConformanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.stub = StubServer()
        self.addCleanup(self.stub.close)
        self.client = MsgEasy("msg_test_key", base_url=self.stub.url, timeout=5)
        self.addCleanup(self.client.close)

    def send(self) -> Any:
        return self.client.messages.send(to="+919876543210", type="text", text="hi")

    # --- Retries -----------------------------------------------------------

    def test_rate_limited_is_retried_after_the_retry_after_header(self) -> None:
        self.stub.error(429, "rate_limited", Retry_After="2")
        self.stub.queue(201, MESSAGE)

        started = time.monotonic()
        message = self.send()
        elapsed = time.monotonic() - started

        self.assertEqual(message.id, "msg_1")
        self.assertEqual(len(self.stub.received), 2)
        # The header, not the 0.5s backoff, decided the wait.
        self.assertGreaterEqual(elapsed, 2)

    def test_key_limit_reached_is_not_retried(self) -> None:
        # A billing cycle away from clearing, so waiting is pointless.
        self.stub.error(403, "key_limit_reached")

        with self.assertRaises(QuotaError) as raised:
            self.send()

        self.assertEqual(raised.exception.code, "key_limit_reached")
        self.assertEqual(len(self.stub.received), 1)

    def test_service_unavailable_is_retried(self) -> None:
        self.stub.error(503, "service_unavailable", Retry_After="1")
        self.stub.queue(201, MESSAGE)

        self.send()

        self.assertEqual(len(self.stub.received), 2)

    def test_meta_error_on_a_write_is_not_retried(self) -> None:
        # The API releases the stored idempotency key on any 5xx, so a retry would
        # re-execute rather than replay — and Meta may already have sent it.
        self.stub.error(502, "meta_error")

        with self.assertRaises(APIError) as raised:
            self.send()

        self.assertEqual(raised.exception.code, "meta_error")
        self.assertEqual(len(self.stub.received), 1)

    def test_idempotency_conflict_still_in_progress_is_retried(self) -> None:
        # `Retry-After: 0` deliberately, matching the TypeScript test: it means
        # retry now, and testing truthiness anywhere in the path would drop it.
        self.stub.error(409, "idempotency_conflict", "still in progress", Retry_After="0")
        self.stub.queue(201, MESSAGE)

        self.send()

        self.assertEqual(len(self.stub.received), 2)

    def test_a_zero_retry_after_is_honoured_rather_than_dropped(self) -> None:
        """`0` is falsy, so a truthiness test would fall back to the backoff."""
        self.stub.error(429, "rate_limited", Retry_After="0")
        self.stub.queue(201, MESSAGE)

        started = time.monotonic()
        self.send()

        self.assertEqual(len(self.stub.received), 2)
        # The 0.5s backoff would be the fallback; honouring 0 waits none of it.
        self.assertLess(time.monotonic() - started, 0.4)

    def test_idempotency_conflict_for_a_different_body_is_not_retried(self) -> None:
        # The same code as above. It carries no `Retry-After`, because only the
        # caller can resolve it by choosing another key.
        self.stub.error(409, "idempotency_conflict", "already used for a different request")

        with self.assertRaises(APIError):
            self.send()

        self.assertEqual(len(self.stub.received), 1)

    def test_gives_up_after_the_third_attempt(self) -> None:
        for _ in range(ATTEMPTS + 1):
            self.stub.error(503, "service_unavailable")

        with self.assertRaises(ServiceUnavailableError):
            self.send()

        # One more was queued than should be consumed, so a fourth attempt would
        # have succeeded and this would not raise.
        self.assertEqual(len(self.stub.received), ATTEMPTS)

    def test_a_connection_fault_is_retried_then_raised_as_a_connection_error(self) -> None:
        # Nothing was received, so the operation may not have run — and the retry
        # carries the original idempotency key, so one that did land replays.
        dead = MsgEasy("msg_test_key", base_url=closed_port_url(), timeout=2)
        self.addCleanup(dead.close)

        with self.assertRaises(APIConnectionError):
            dead.messages.send(to="+919876543210", type="text", text="hi")

    # --- Idempotency -------------------------------------------------------

    def test_two_attempts_of_one_send_carry_the_same_idempotency_key(self) -> None:
        self.stub.error(503, "service_unavailable", Retry_After="1")
        self.stub.queue(201, MESSAGE)

        self.send()

        keys = {request.headers[IDEMPOTENCY_KEY] for request in self.stub.received}
        self.assertEqual(len(keys), 1)

    def test_a_read_sends_no_idempotency_key(self) -> None:
        self.stub.queue(200, MESSAGE)

        self.client.messages.get("msg_1")

        self.assertNotIn(IDEMPOTENCY_KEY, self.stub.received[0].headers)

    # --- Errors ------------------------------------------------------------

    def test_every_error_carries_the_request_id(self) -> None:
        self.stub.error(404, "not_found")

        with self.assertRaises(NotFoundError) as raised:
            self.client.messages.get("msg_missing")

        self.assertEqual(raised.exception.request_id, "req_stub")

    def test_an_unrecognised_code_is_surfaced_not_raised_as_a_crash(self) -> None:
        # The catalogue grows every phase. An older SDK has to pass a code it does
        # not know through to the caller.
        self.stub.error(403, "a_code_from_a_later_phase")

        with self.assertRaises(APIError) as raised:
            self.send()

        self.assertIs(type(raised.exception), APIError)
        self.assertEqual(raised.exception.code, "a_code_from_a_later_phase")
        # Unknown, so not retryable: only codes we recognise are waited out.
        self.assertEqual(len(self.stub.received), 1)

    def test_a_response_value_from_a_later_phase_does_not_raise(self) -> None:
        # The generated models would otherwise reject a status added after this
        # release, on a perfectly successful read.
        self.stub.queue(201, {**MESSAGE, "status": "a_status_from_a_later_phase"})

        self.assertEqual(self.send().status, "a_status_from_a_later_phase")

    def test_a_response_enum_still_carries_its_values_in_the_type(self) -> None:
        # Widening must not cost the values: an editor should still complete them,
        # which is what the TypeScript union gives and what a bare `str` would not.
        annotation = get_type_hints(Message)["status"]
        literals = next(arg for arg in get_args(annotation) if get_origin(arg) is Literal)

        self.assertEqual(get_args(literals), ("accepted", "sent", "delivered", "read", "failed"))
        # And `str` alongside them, which is what lets an unknown value through.
        self.assertIn(str, get_args(annotation))

    def test_a_request_field_is_still_validated(self) -> None:
        # The other half of that trade: validating what the caller passes is
        # useful, and cannot break on a value the API invented later.
        with self.assertRaises(ValidationError):
            self.client.messages.send(to="+919876543210", type="carrier_pigeon")

        self.assertEqual(self.stub.received, [])

    def test_a_template_header_still_resolves_to_its_variant(self) -> None:
        # `header` is a `oneOf`. Its variants are widened too, and the generator
        # tells them apart by their required fields — `text` against `mediaId` —
        # so a header type Meta adds later deserialises rather than raising.
        self.stub.queue(200, template("tpl_1", header={"type": "TEXT", "text": "Hi"}))
        self.stub.queue(200, template("tpl_2", header={"type": "IMAGE", "mediaId": "med_1"}))
        self.stub.queue(200, template("tpl_3", header={"type": "AUDIO", "mediaId": "med_1"}))

        text = self.client.templates.get("tpl_1")
        media = self.client.templates.get("tpl_2")
        later = self.client.templates.get("tpl_3")

        assert text.header is not None and media.header is not None
        assert later.header is not None and later.header.actual_instance is not None
        self.assertIsInstance(text.header.actual_instance, TextHeader)
        self.assertIsInstance(media.header.actual_instance, MediaHeader)
        self.assertEqual(later.header.actual_instance.type, "AUDIO")

    def test_a_refusal_that_is_not_our_envelope_still_raises_cleanly(self) -> None:
        # A proxy between the caller and us, answering with its own error page.
        # Its own class, not an `APIError` with a missing `code`: a caller branching
        # on `code` must never be handed an absence where a code belongs.
        self.stub.queue(502, "<html>bad gateway</html>")

        with self.assertRaises(BadEnvelopeError) as raised:
            self.client.messages.get("msg_1")

        self.assertEqual(raised.exception.status, 502)
        self.assertNotIsInstance(raised.exception, APIError)
        self.assertFalse(hasattr(raised.exception, "code"))

    # --- Auth, identity, limits -------------------------------------------

    def test_every_request_carries_the_key_and_a_named_user_agent(self) -> None:
        self.stub.queue(200, MESSAGE)

        self.client.messages.get("msg_1")

        sent = self.stub.received[0].headers
        self.assertEqual(sent["x-api-key"], "msg_test_key")
        self.assertTrue(sent["User-Agent"].startswith("msgeasy-python/"))

    def test_rate_limit_headers_are_exposed_on_the_response_and_the_error(self) -> None:
        self.stub.queue(
            200, MESSAGE, X_RateLimit_Limit="60", X_RateLimit_Remaining="59", X_RateLimit_Reset="30"
        )
        self.client.messages.get("msg_1")

        reported = self.client.rate_limit
        assert reported is not None
        self.assertEqual(reported.remaining, 59)

        # A refusal carries them too, which is the case a caller most needs: it
        # says how long until the allowance is worth trying again.
        self.stub.error(
            403,
            "key_limit_reached",
            X_RateLimit_Limit="60",
            X_RateLimit_Remaining="0",
            X_RateLimit_Reset="12",
        )
        with self.assertRaises(QuotaError) as raised:
            self.client.messages.get("msg_1")

        refused = raised.exception.rate_limit
        assert refused is not None
        self.assertEqual(refused.remaining, 0)

    def test_rate_limit_is_none_when_the_response_omits_the_headers(self) -> None:
        # A key with no configured ceiling, or a refusal that never reached the
        # limiter. Unknown, not "nothing left".
        self.stub.queue(200, MESSAGE)

        self.client.messages.get("msg_1")

        self.assertIsNone(self.client.rate_limit)

    # --- Pagination --------------------------------------------------------

    def test_a_list_yields_every_item_once_and_stops(self) -> None:
        self.stub.queue(200, {"data": [template("tpl_1"), template("tpl_2")], "has_more": True})
        self.stub.queue(200, {"data": [template("tpl_3")], "has_more": False})

        found = [item.id for item in self.client.templates.list_all()]

        self.assertEqual(found, ["tpl_1", "tpl_2", "tpl_3"])
        # The second page asked to start after the last id of the first.
        self.assertIn("starting_after=tpl_2", self.stub.received[1].path)

    def test_a_list_puts_every_filter_on_the_query_string(self) -> None:
        self.stub.queue(200, {"data": [template("tpl_1")], "has_more": False})

        list(self.client.templates.list_all(status="approved", limit=5, updated_after="2026-09-01"))

        path = self.stub.received[0].path
        for expected in ("status=approved", "limit=5", "updatedAfter=2026-09-01"):
            self.assertIn(expected, path)

    def test_a_list_carries_its_filters_onto_every_page(self) -> None:
        # A filter dropped after page one would silently widen the result set.
        self.stub.queue(200, {"data": [template("tpl_1")], "has_more": True})
        self.stub.queue(200, {"data": [template("tpl_2")], "has_more": False})

        list(self.client.templates.list_all(status="approved", limit=1))

        first, second = (request.path for request in self.stub.received)
        self.assertIn("status=approved", second)
        self.assertIn("limit=1", second)
        self.assertNotIn("starting_after", first)
        self.assertIn("starting_after=tpl_1", second)

    def test_a_page_is_returned_as_it_came_with_the_cursor_the_caller_passed(self) -> None:
        # `list` is one page and `list_all` iterates; they are separate methods
        # because TypeScript's `list` means the page.
        self.stub.queue(200, {"data": [template("tpl_2")], "has_more": True})

        page = self.client.templates.list(limit=1, starting_after="tpl_1")

        self.assertEqual([item.id for item in page.data], ["tpl_2"])
        self.assertTrue(page.has_more)
        path = self.stub.received[0].path
        self.assertIn("starting_after=tpl_1", path)
        self.assertIn("limit=1", path)

    def test_a_list_stops_on_an_empty_page_that_claims_more(self) -> None:
        # Without this the cursor would never advance and the loop would not end.
        self.stub.queue(200, {"data": [], "has_more": True})

        self.assertEqual(list(self.client.templates.list_all()), [])
        self.assertEqual(len(self.stub.received), 1)

    # --- Media -------------------------------------------------------------

    def test_an_upload_sends_the_file_as_multipart_with_an_idempotency_key(self) -> None:
        self.stub.queue(201, MEDIA)

        media = self.client.media.upload(b"hello", filename="hello.txt")

        self.assertEqual(media.id, "med_1")
        request = self.stub.received[0]
        self.assertTrue(request.headers["Content-Type"].startswith("multipart/form-data"))
        self.assertIn(b"hello", request.body)
        self.assertIn(b'filename="hello.txt"', request.body)
        # The file is part of the fingerprint, so a retried upload replays rather
        # than storing a second copy.
        self.assertIn(IDEMPOTENCY_KEY, request.headers)

    def test_a_retried_upload_resends_the_file_and_its_multipart_headers(self) -> None:
        # The upload builds its own request, so a retry has to rebuild it rather
        # than replay a half-consumed one.
        self.stub.error(503, "service_unavailable", Retry_After="1")
        self.stub.queue(201, MEDIA)

        self.client.media.upload(b"hello", filename="hello.txt")

        self.assertEqual(len(self.stub.received), 2)
        for request in self.stub.received:
            self.assertTrue(request.headers["Content-Type"].startswith("multipart/form-data"))
            self.assertIn(b'filename="hello.txt"', request.body)

    def test_a_server_that_never_answers_times_out(self) -> None:
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(ATTEMPTS)
        self.addCleanup(listener.close)
        # Accepts the connections and answers none of them.
        threading.Thread(
            target=lambda: [listener.accept() for _ in range(ATTEMPTS)], daemon=True
        ).start()

        stalled = MsgEasy(
            "msg_test_key", base_url=f"http://127.0.0.1:{listener.getsockname()[1]}", timeout=0.2
        )
        self.addCleanup(stalled.close)

        with self.assertRaises(APIConnectionError):
            stalled.messages.get("msg_1")

    def test_an_upload_of_bytes_without_a_filename_is_refused_locally(self) -> None:
        with self.assertRaises(ValueError):
            self.client.media.upload(b"hello")

        self.assertEqual(self.stub.received, [])


class EventLoopWarningTest(unittest.TestCase):
    """
    The client is synchronous, so a call inside `async def` freezes the loop and
    every other request on the worker with it — silently, since nothing fails.
    The warning is the only signal, so these pin exactly when it fires.
    """

    def setUp(self) -> None:
        self.stub = StubServer()
        self.addCleanup(self.stub.close)
        self.client = MsgEasy("msg_test_key", base_url=self.stub.url, timeout=5)
        self.addCleanup(self.client.close)

    def send(self) -> Any:
        return self.client.messages.send(to="+919876543210", type="text", text="hi")

    def test_no_warning_off_the_event_loop(self) -> None:
        self.stub.queue(201, MESSAGE)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self.send()
        self.assertEqual([w for w in caught if w.category is RuntimeWarning], [])

    def test_warns_when_called_on_the_event_loop(self) -> None:
        self.stub.queue(201, MESSAGE)

        async def on_the_loop() -> Any:
            return self.send()

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            asyncio.run(on_the_loop())

        runtime = [w for w in caught if w.category is RuntimeWarning]
        self.assertEqual(len(runtime), 1)
        self.assertIn("blocks the event loop", str(runtime[0].message))

    def test_no_warning_when_run_off_the_loop_in_a_thread(self) -> None:
        """`to_thread` is one of the two fixes the message names, so it must be quiet."""
        self.stub.queue(201, MESSAGE)

        async def off_the_loop() -> Any:
            return await asyncio.to_thread(self.send)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            asyncio.run(off_the_loop())
        self.assertEqual([w for w in caught if w.category is RuntimeWarning], [])

    def assert_blames_the_caller(self, call: Callable[[], Any]) -> None:
        """Runs `call` on a loop and checks the one warning points at its own line."""

        async def on_the_loop() -> Any:
            return call()

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            asyncio.run(on_the_loop())

        # Filtered rather than indexed: an unrelated `DeprecationWarning` from a
        # dependency would otherwise take slot zero and be asserted against.
        runtime = [w for w in caught if w.category is RuntimeWarning]
        self.assertEqual(len(runtime), 1)
        self.assertEqual(runtime[0].filename, __file__)
        # A lambda's first line is the line it was written on, which is the call
        # site. Read from the code object rather than written down, so the
        # assertion survives an edit further up the file.
        # Cast because a lambda is typed as `Callable`, which carries no
        # `__code__`, though every lambda passed here is a function.
        self.assertEqual(runtime[0].lineno, cast(FunctionType, call).__code__.co_firstlineno)

    def test_the_warning_points_at_the_caller(self) -> None:
        """Blamed on the line that made the call, not on the SDK's own internals."""
        self.stub.queue(201, MESSAGE)
        # Not `self.send()`: the walk stops at the first frame outside the package,
        # which would be that helper rather than the lambda being asserted on.
        self.assert_blames_the_caller(
            lambda: self.client.messages.send(to="+919876543210", type="text", text="hi")
        )

    def test_the_warning_points_at_the_caller_of_a_paged_method(self) -> None:
        """
        `templates.list` reaches the transport through `_page`, and `list_all`
        through `_page`, a lambda and `paginate` — one and three frames deeper
        than every other method. A fixed `stacklevel` blames the SDK's own file
        here, and the default filter then registers the warning against that line,
        silencing every other blocking call site in the process.
        """
        page = {"data": [template("tpl_1")], "has_more": False}

        self.stub.queue(200, page)
        self.assert_blames_the_caller(lambda: self.client.templates.list())

        self.stub.queue(200, page)
        self.assert_blames_the_caller(lambda: list(self.client.templates.list_all()))


class ErrorTreeTest(unittest.TestCase):
    """
    The tree is the contract with the TypeScript SDK. A code mapped to a different
    class in one language is a divergence nothing else would catch.
    """

    def setUp(self) -> None:
        self.stub = StubServer()
        self.addCleanup(self.stub.close)
        self.client = MsgEasy("msg_test_key", base_url=self.stub.url, timeout=5)
        self.addCleanup(self.client.close)

    def test_every_documented_code_raises_its_mapped_class(self) -> None:
        expected = {
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

        for code, expected_class in expected.items():
            with self.subTest(code=code):
                # A non-retryable code leaves the extra replies queued, so clear
                # before each one rather than letting them spill into the next.
                self.stub.queued.clear()
                # 400 throughout: the class comes from `code`, never from the status.
                # Queued once per attempt, since the retryable codes exhaust the
                # queue otherwise; `Retry-After: 0` keeps that from sleeping.
                for _ in range(ATTEMPTS):
                    self.stub.queue(400, {"code": code, "message": "refused"}, Retry_After="0")
                with self.assertRaises(expected_class):
                    self.client.messages.get("msg_1")

    def test_an_unrecognised_code_raises_plain_api_error(self) -> None:
        self.stub.queue(400, {"code": "invented_last_tuesday", "message": "refused"})

        with self.assertRaises(APIError) as raised:
            self.client.messages.get("msg_1")

        self.assertIs(type(raised.exception), APIError)
        self.assertEqual(raised.exception.code, "invented_last_tuesday")

    def test_one_base_catches_everything(self) -> None:
        self.stub.error(404, "not_found")

        with self.assertRaises(MsgEasyError):
            self.client.messages.get("msg_1")


class IdempotencyKeyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.stub = StubServer()
        self.addCleanup(self.stub.close)
        self.client = MsgEasy("msg_test_key", base_url=self.stub.url, timeout=5)
        self.addCleanup(self.client.close)

    def send(self, **kwargs: Any) -> Any:
        return self.client.messages.send(to="+919876543210", type="text", text="hi", **kwargs)

    def test_the_callers_own_key_is_sent_rather_than_a_minted_one(self) -> None:
        self.stub.queue(201, MESSAGE)

        self.send(idempotency_key="my-own-key")

        self.assertEqual(self.stub.received[0].headers["Idempotency-Key"], "my-own-key")

    def test_that_key_survives_a_retry(self) -> None:
        self.stub.error(429, "rate_limited", Retry_After="0")
        self.stub.queue(201, MESSAGE)

        self.send(idempotency_key="survives")

        keys = [r.headers["Idempotency-Key"] for r in self.stub.received]
        self.assertEqual(keys, ["survives", "survives"])

    def test_a_key_over_255_characters_is_refused_without_a_request(self) -> None:
        with self.assertRaises(ValueError):
            self.send(idempotency_key="x" * 256)

        self.assertEqual(self.stub.received, [])

    def test_a_read_sends_none(self) -> None:
        self.stub.queue(200, MESSAGE)

        self.client.messages.get("msg_1")

        self.assertNotIn("Idempotency-Key", self.stub.received[0].headers)


class OnResponseTest(unittest.TestCase):
    """
    The methods return the parsed body and nothing else, so this hook is the only
    way to see the wire. These pin what reaches it.
    """

    def setUp(self) -> None:
        self.stub = StubServer()
        self.addCleanup(self.stub.close)
        self.events: List[RequestEvent] = []
        self.client = MsgEasy(
            "msg_test_key",
            base_url=self.stub.url,
            timeout=5,
            on_response=self.events.append,
        )
        self.addCleanup(self.client.close)

    def send(self, **kwargs: Any) -> Any:
        return self.client.messages.send(to="+919876543210", type="text", text="hi", **kwargs)

    def test_it_fires_once_per_attempt_so_a_retry_is_two_rows(self) -> None:
        self.stub.error(429, "rate_limited", Retry_After="0")
        self.stub.queue(201, MESSAGE)

        self.send()

        self.assertEqual([(e.attempt, e.status) for e in self.events], [(1, 429), (2, 201)])

    def test_it_carries_both_bodies_as_they_were_on_the_wire(self) -> None:
        self.stub.queue(201, MESSAGE)

        self.send()

        self.assertEqual(self.events[0].request_body["text"], "hi")
        self.assertEqual(self.events[0].response_body["id"], MESSAGE["id"])

    def test_it_carries_the_request_id_on_a_success(self) -> None:
        # The one thing a successful call cannot otherwise give you, and the only
        # thing support can trace.
        self.stub.queue(201, MESSAGE)

        self.send()

        self.assertEqual(self.events[0].request_id, "req_stub")

    def test_it_carries_the_idempotency_key_actually_sent(self) -> None:
        self.stub.queue(201, MESSAGE)

        self.send(idempotency_key="seen-it")

        self.assertEqual(self.events[0].idempotency_key, "seen-it")

    def test_it_fires_on_a_refusal_too(self) -> None:
        self.stub.error(404, "not_found")

        with self.assertRaises(NotFoundError):
            self.client.messages.get("msg_1")

        self.assertEqual(self.events[0].status, 404)
        self.assertEqual(self.events[0].response_body["code"], "not_found")

    def test_it_fires_with_no_status_when_nothing_came_back(self) -> None:
        # Nothing listens on this port, so the connection is refused outright.
        events: List[RequestEvent] = []
        client = MsgEasy(
            "msg_test_key", base_url="http://127.0.0.1:1", timeout=2, on_response=events.append
        )
        self.addCleanup(client.close)

        with self.assertRaises(APIConnectionError):
            client.messages.get("msg_1")

        self.assertIsNone(events[0].status)
        self.assertTrue(events[0].transport_error)

    def test_a_raising_handler_does_not_break_the_call(self) -> None:
        def explode(_: RequestEvent) -> None:
            raise RuntimeError("the hook observes; it does not get a vote")

        client = MsgEasy("msg_test_key", base_url=self.stub.url, timeout=5, on_response=explode)
        self.addCleanup(client.close)
        self.stub.queue(200, MESSAGE)

        with self.assertLogs("msgeasy", level="WARNING"):
            self.assertEqual(client.messages.get("msg_1").id, MESSAGE["id"])

    def test_reading_the_body_leaves_it_readable_by_the_sdk(self) -> None:
        self.stub.queue(200, MESSAGE)

        message = self.client.messages.get("msg_1")

        self.assertEqual(message.id, MESSAGE["id"])
        self.assertEqual(len(self.events), 1)


class ReviewFixTest(unittest.TestCase):
    """Each of these pins a defect found reviewing the first cut of this work."""

    def setUp(self) -> None:
        self.stub = StubServer()
        self.addCleanup(self.stub.close)
        self.client = MsgEasy("msg_test_key", base_url=self.stub.url, timeout=5)
        self.addCleanup(self.client.close)

    def test_an_empty_idempotency_key_is_refused_not_replaced(self) -> None:
        # Silently minting one would leave the caller believing they hold a key
        # they can replay.
        with self.assertRaises(MsgEasyValidationError):
            self.client.messages.send(
                to="+919876543210", type="text", text="hi", idempotency_key=""
            )

        self.assertEqual(self.stub.received, [])

    def test_local_refusals_are_catchable_as_sdk_errors(self) -> None:
        # The base is documented as catching everything the SDK raises.
        with self.assertRaises(MsgEasyError):
            self.client.messages.send(
                to="+919876543210", type="text", text="hi", idempotency_key="x" * 256
            )

    def test_a_body_that_is_not_an_object_does_not_crash(self) -> None:
        self.stub.queue(502, None)

        with self.assertRaises(MsgEasyError):
            self.client.messages.get("msg_1")


if __name__ == "__main__":
    unittest.main()
