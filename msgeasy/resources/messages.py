"""Sending WhatsApp messages and reading their delivery status."""

from __future__ import annotations

from typing import Dict, Optional

from msgeasy._generated.api.messages_api import MessagesApi
from msgeasy._generated.models.message import Message
from msgeasy._generated.models.send_message_input import SendMessageInput
from msgeasy._transport import Transport


class MessagesResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._api = MessagesApi(transport.api_client)

    def send(
        self,
        *,
        to: str,
        type: str,
        text: Optional[str] = None,
        template_id: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None,
        media_id: Optional[str] = None,
        caption: Optional[str] = None,
        reply_to: Optional[str] = None,
        timeout: Optional[float] = None,
        idempotency_key: Optional[str] = None,
    ) -> Message:
        """
        Sends a message. A template may go at any time; `text` and `media` only
        within 24 hours of the recipient's last inbound message.
        """
        return self._transport.call(
            self._api.messages_send_with_http_info,
            send_message_input=SendMessageInput(
                to=to,
                type=type,
                text=text,
                template_id=template_id,
                variables=variables,
                media_id=media_id,
                caption=caption,
                reply_to=reply_to,
            ),
            idempotent=True,
            timeout=timeout,
            idempotency_key=idempotency_key,
        )

    def get(self, message_id: str, *, timeout: Optional[float] = None) -> Message:
        """Reads a message's current delivery status."""
        return self._transport.call(
            self._api.messages_get_with_http_info,
            id=message_id,
            idempotent=False,
            timeout=timeout,
        )
