"""
A scripted HTTP server, so the conformance scenarios run against real sockets.

`docs/sdk/sdk-conformance.md` section 12 requires both SDKs to run the same
scenarios against a stub. Anything faked below the socket — a patched transport,
a mocked urllib3 — would stop testing the part most likely to be wrong: which
headers actually go out, and what the client does with the ones that come back.
"""

from __future__ import annotations

import json
import threading
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Deque, Dict, List, Optional, cast


class Response:
    def __init__(
        self, status: int, body: Any = None, headers: Optional[Dict[str, str]] = None
    ) -> None:
        self.status = status
        self.body = body
        self.headers = headers or {}


class Request:
    def __init__(self, method: str, path: str, headers: Dict[str, str], body: bytes) -> None:
        self.method = method
        self.path = path
        self.headers = headers
        self.body = body

    @property
    def json(self) -> Any:
        return json.loads(self.body)


class StubServer:
    """Answers with whatever was queued, and records what it was asked."""

    def __init__(self) -> None:
        self.queued: Deque[Response] = deque()
        self.received: List[Request] = []
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _handler_for(self))
        # Keep-alive leaves a handler thread parked on a socket; without this the
        # server waits for it on every teardown.
        self._server.daemon_threads = True
        # `shutdown` waits for the next poll, and the default interval is half a
        # second — per test, across the whole suite.
        self._thread = threading.Thread(
            target=self._server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
        )
        self._thread.start()

    @property
    def url(self) -> str:
        host, port = cast("tuple[str, int]", self._server.server_address[:2])
        return f"http://{host}:{port}"

    def queue(self, status: int, body: Any = None, **headers: str) -> None:
        self.queued.append(Response(status, body, headers))

    def error(self, status: int, code: str, message: str = "refused", **headers: str) -> None:
        """Queues the `/v1` error envelope, which every refusal carries."""
        self.queued.append(
            Response(
                status,
                {"statusCode": status, "error": "Error", "message": message, "code": code},
                headers,
            )
        )

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


def _handler_for(stub: StubServer) -> type:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def _respond(self) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            stub.received.append(
                Request(self.command, self.path, dict(self.headers), self.rfile.read(length))
            )

            queued = stub.queued.popleft() if stub.queued else Response(500, {"code": "unscripted"})
            payload = b"" if queued.body is None else json.dumps(queued.body).encode()

            self.send_response(queued.status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            # Sent on every `/v1` response, so every error can carry it.
            self.send_header("X-Request-Id", "req_stub")
            for name, value in queued.headers.items():
                self.send_header(name.replace("_", "-"), value)
            self.end_headers()
            self.wfile.write(payload)

        do_GET = do_POST = do_PATCH = _respond

        def log_message(self, *args: Any) -> None:
            """Silent: the suite's output is the assertions, not an access log."""

    return Handler
