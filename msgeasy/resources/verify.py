"""One-time passcodes over WhatsApp."""

from __future__ import annotations

from typing import Optional

from msgeasy._generated.api.verify_api import VerifyApi
from msgeasy._generated.models.check_verification_input import CheckVerificationInput
from msgeasy._generated.models.start_verification_input import StartVerificationInput
from msgeasy._generated.models.verification import Verification
from msgeasy._generated.models.verification_check import VerificationCheck
from msgeasy._transport import Transport


class VerifyResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._api = VerifyApi(transport.api_client)

    def start(
        self,
        *,
        phone: str,
        channel: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        code_length: Optional[int] = None,
        timeout: Optional[float] = None,
        idempotency_key: Optional[str] = None,
    ) -> Verification:
        """
        Sends a code and returns the id to check it against. A `test` key returns
        the code in `code`, so no real handset is involved.
        """
        return self._transport.call(
            self._api.verify_start_with_http_info,
            start_verification_input=StartVerificationInput(
                phone=phone,
                channel=channel,
                ttl_seconds=ttl_seconds,
                code_length=code_length,
            ),
            idempotent=True,
            timeout=timeout,
            idempotency_key=idempotency_key,
        )

    def check(
        self,
        *,
        verification_id: str,
        code: str,
        timeout: Optional[float] = None,
        idempotency_key: Optional[str] = None,
    ) -> VerificationCheck:
        """
        Checks a code. A wrong one is not an error — it returns `status`
        "invalid" with the attempts left.
        """
        return self._transport.call(
            self._api.verify_check_with_http_info,
            check_verification_input=CheckVerificationInput(
                verification_id=verification_id, code=code
            ),
            idempotent=True,
            timeout=timeout,
            idempotency_key=idempotency_key,
        )
