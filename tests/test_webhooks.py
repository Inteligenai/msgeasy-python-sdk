"""
Webhook signature verification.

The vector below was produced by the API's own `signWebhook`
(`apps/api/src/lib/webhooks/signature.ts`), not by this package. That is the
point: the two implementations sign independently, and if they ever disagree
every delivery to a Python endpoint would be rejected.
"""

from __future__ import annotations

import unittest
from typing import Any, Dict, Optional, Union

from msgeasy import SignatureResult, verify_webhook_signature

BODY = '{"event":"message.delivered","id":"msg_1"}'
SECRET = "whsec_test_secret"
HEADER = "t=1757239200,v1=AnMRzi6eA9I0R/OggbX7T4Lh4ThieWBekFD3tVUbPhk="
SIGNED_AT = 1757239200


class WebhookSignatureTest(unittest.TestCase):
    def verify(
        self,
        body: Union[str, bytes] = BODY,
        header: str = HEADER,
        secret: str = SECRET,
        now: float = SIGNED_AT,
    ) -> SignatureResult:
        return verify_webhook_signature(body, header, secret, now=now)

    def test_accepts_what_the_api_signed(self) -> None:
        self.assertTrue(self.verify())

    def test_accepts_the_raw_bytes_a_framework_hands_over(self) -> None:
        self.assertTrue(self.verify(body=BODY.encode("utf-8")))

    def test_rejects_a_tampered_body(self) -> None:
        self.assertFalse(self.verify(body=BODY.replace("msg_1", "msg_2")))

    def test_rejects_a_body_that_was_reserialized(self) -> None:
        # The trap worth having a test for: same data, different bytes.
        self.assertFalse(self.verify(body='{"event": "message.delivered", "id": "msg_1"}'))

    def test_rejects_the_wrong_secret(self) -> None:
        self.assertFalse(self.verify(secret="whsec_other"))

    def test_rejects_a_delivery_older_than_the_tolerance(self) -> None:
        # Signed six minutes ago, against a five-minute window.
        self.assertFalse(self.verify(now=SIGNED_AT + 360))
        self.assertTrue(self.verify(now=SIGNED_AT + 299))

    def test_rejects_a_clock_far_ahead_of_us(self) -> None:
        self.assertFalse(self.verify(now=SIGNED_AT - 360))

    def test_rejects_a_missing_or_malformed_header(self) -> None:
        for header in ("", "nonsense", "t=1757239200", "v1=abc", "t=later,v1=abc"):
            with self.subTest(header=header):
                self.assertFalse(self.verify(header=header))

        self.assertFalse(verify_webhook_signature(BODY, None, SECRET))

    def test_reads_the_fields_in_either_order(self) -> None:
        reversed_header = "v1=AnMRzi6eA9I0R/OggbX7T4Lh4ThieWBekFD3tVUbPhk=,t=1757239200"

        self.assertTrue(self.verify(header=reversed_header))

    def test_honours_a_widened_tolerance(self) -> None:
        self.assertTrue(
            verify_webhook_signature(
                BODY, HEADER, SECRET, tolerance_seconds=3600, now=SIGNED_AT + 1800
            )
        )


if __name__ == "__main__":
    unittest.main()


class SignatureReasonTest(unittest.TestCase):
    """
    A bare False cannot be logged or acted on: "stale clock" and "wrong secret"
    need different answers from whoever is on call.
    """

    def reason(self, **kwargs: Any) -> Optional[str]:
        defaults: Dict[str, Any] = {
            "body": BODY,
            "headers": HEADER,
            "secret": SECRET,
            "now": SIGNED_AT,
        }
        defaults.update(kwargs)
        body = defaults.pop("body")
        headers = defaults.pop("headers")
        secret = defaults.pop("secret")
        return verify_webhook_signature(body, headers, secret, **defaults).reason

    def test_each_refusal_says_which_one_it_was(self) -> None:
        self.assertIsNone(self.reason())
        self.assertEqual(self.reason(secret=""), "no_secret_configured")
        self.assertEqual(self.reason(headers=None), "missing_header")
        self.assertEqual(self.reason(headers=""), "missing_header")
        self.assertEqual(self.reason(headers="garbage"), "malformed_header")
        self.assertEqual(self.reason(now=SIGNED_AT + 10_000), "stale_timestamp")
        self.assertEqual(self.reason(secret="wrong"), "bad_signature")

    def test_it_finds_the_header_in_a_framework_header_map(self) -> None:
        # Node lower-cases inbound header names and Python frameworks are
        # case-insensitive, so the lookup has to be too.
        for name in ("x-msgeasy-signature", "X-Msgeasy-Signature", "X-MSGEASY-SIGNATURE"):
            with self.subTest(name=name):
                self.assertTrue(
                    verify_webhook_signature(BODY, {name: HEADER}, SECRET, now=SIGNED_AT)
                )

    def test_a_header_map_without_the_signature_is_missing_not_malformed(self) -> None:
        result = verify_webhook_signature(BODY, {"content-type": "application/json"}, SECRET)

        self.assertEqual(result.reason, "missing_header")

    def test_a_header_that_arrived_twice_is_refused(self) -> None:
        """
        Some frameworks hand a repeated header over as a list; a proxy may instead
        join them with a comma. Either way two signatures is not one delivery to
        trust, and neither may reach `.split()` and raise inside a handler.
        """
        twice = verify_webhook_signature(BODY, {"x-msgeasy-signature": [HEADER, HEADER]}, SECRET)
        self.assertEqual(twice.reason, "malformed_header")
        self.assertEqual(
            self.reason(headers=f"t=1000,v1=BOGUS, {HEADER}"),
            "malformed_header",
        )
        # A second `v1` with no value at all still counts as a second signature.
        self.assertEqual(self.reason(headers=f"{HEADER},v1"), "malformed_header")
