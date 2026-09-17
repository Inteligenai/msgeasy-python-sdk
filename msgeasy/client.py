"""The client a developer constructs, and the only thing they need to configure."""

from __future__ import annotations

from types import TracebackType
from typing import Optional, Type

from msgeasy import _observe
from msgeasy._events import ResponseHandler
from msgeasy._generated.api_client import ApiClient
from msgeasy._generated.configuration import Configuration
from msgeasy._headers import RateLimit
from msgeasy._policy import DEFAULT_TIMEOUT_SECONDS
from msgeasy._transport import Transport
from msgeasy._version import __version__
from msgeasy.resources import (
    MediaResource,
    MessagesResource,
    TemplatesResource,
    VerifyResource,
)

#: Identifies the SDK and its version in our request log, so a support ticket can
#: be traced to a release.
USER_AGENT = f"msgeasy-python/{__version__}"

_AUTH_SCHEME = "apiKeyAuth"


class MsgEasy:
    """
    Talks to the MsgEasy `/v1` API.

    The key is a server-side secret. A `msg_test_` key runs every request the
    same way but delivers nothing and is never billed.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        on_response: Optional[ResponseHandler] = None,
    ) -> None:
        """`on_response` is called once per attempt. See `RequestEvent`."""
        configuration = Configuration(
            host=base_url,
            api_key={_AUTH_SCHEME: api_key},
            # Retries belong to `_policy`. Left to urllib3, a read would also be
            # retried three times inside each of those attempts.
            retries=0,
        )
        api_client = ApiClient(configuration)
        api_client.user_agent = USER_AGENT
        if on_response is not None:
            _observe.install(api_client, on_response)

        self._transport = Transport(api_client, timeout)
        self.verify = VerifyResource(self._transport)
        self.messages = MessagesResource(self._transport)
        self.media = MediaResource(self._transport)
        self.templates = TemplatesResource(self._transport)

    @property
    def rate_limit(self) -> Optional[RateLimit]:
        """What the most recent response reported, or `None` until one does."""
        return self._transport.rate_limit

    def close(self) -> None:
        """Releases the pooled connections. Optional — a dropped client is
        collected."""
        self._transport.api_client.rest_client.pool_manager.clear()

    def __enter__(self) -> "MsgEasy":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.close()
