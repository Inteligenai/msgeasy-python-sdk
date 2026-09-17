"""
The MsgEasy Python SDK — WhatsApp messaging and one-time passcodes.

    client = MsgEasy("msg_test_...")
    client.verify.start(phone="+919876543210")
"""

# Request and response shapes, generated from the same OpenAPI document the API
# serves, so they cannot drift from it.
from msgeasy._events import RequestEvent
from msgeasy._generated.models.media import Media
from msgeasy._generated.models.media_header import MediaHeader
from msgeasy._generated.models.media_header_input import MediaHeaderInput
from msgeasy._generated.models.message import Message
from msgeasy._generated.models.message_error import MessageError
from msgeasy._generated.models.template import Template
from msgeasy._generated.models.template_header import TemplateHeader
from msgeasy._generated.models.template_header_input import TemplateHeaderInput
from msgeasy._generated.models.template_issue import TemplateIssue
from msgeasy._generated.models.template_validation import TemplateValidation
from msgeasy._generated.models.template_variable import TemplateVariable
from msgeasy._generated.models.template_variable_input import TemplateVariableInput
from msgeasy._generated.models.text_header import TextHeader
from msgeasy._generated.models.text_header_input import TextHeaderInput
from msgeasy._generated.models.verification import Verification
from msgeasy._generated.models.verification_check import VerificationCheck
from msgeasy._headers import RateLimit
from msgeasy._version import __version__
from msgeasy.client import MsgEasy
from msgeasy.errors import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    BadEnvelopeError,
    IdempotencyError,
    InvalidRequestError,
    MetaError,
    MsgEasyError,
    NotFoundError,
    PermissionDeniedError,
    QuotaError,
    RateLimitError,
    ServiceUnavailableError,
    SetupRequiredError,
    TemplateError,
    TestKeyError,
    ValidationError,
    WindowExpiredError,
)
from msgeasy.webhooks import (
    DEFAULT_TOLERANCE_SECONDS,
    SIGNATURE_HEADER,
    SignatureResult,
    verify_webhook_signature,
)

__all__ = [
    "MsgEasy",
    "RateLimit",
    "RequestEvent",
    "verify_webhook_signature",
    "SIGNATURE_HEADER",
    "SignatureResult",
    "DEFAULT_TOLERANCE_SECONDS",
    "__version__",
    # Errors
    "MsgEasyError",
    "APIConnectionError",
    "APIError",
    "BadEnvelopeError",
    "ValidationError",
    "AuthenticationError",
    "PermissionDeniedError",
    "RateLimitError",
    "QuotaError",
    "SetupRequiredError",
    "NotFoundError",
    "InvalidRequestError",
    "IdempotencyError",
    "WindowExpiredError",
    "TemplateError",
    "MetaError",
    "ServiceUnavailableError",
    "TestKeyError",
    # Shapes
    "TemplateHeaderInput",
    "TextHeaderInput",
    "MediaHeaderInput",
    "TemplateVariableInput",
    "TemplateHeader",
    "TextHeader",
    "MediaHeader",
    "TemplateVariable",
    "Media",
    "Message",
    "MessageError",
    "Template",
    "TemplateValidation",
    "TemplateIssue",
    "Verification",
    "VerificationCheck",
]
