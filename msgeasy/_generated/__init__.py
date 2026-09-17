# coding: utf-8

# flake8: noqa

"""MsgEasy WhatsApp API"""  # noqa: E501


__version__ = "0.1.0"

# Define package exports
__all__ = [
    "MediaApi",
    "MessagesApi",
    "TemplatesApi",
    "VerifyApi",
    "ApiResponse",
    "ApiClient",
    "Configuration",
    "OpenApiException",
    "ApiTypeError",
    "ApiValueError",
    "ApiKeyError",
    "ApiAttributeError",
    "ApiException",
    "ApiError",
    "CheckVerificationInput",
    "CreateTemplateInput",
    "Media",
    "MediaHeader",
    "MediaHeaderInput",
    "Message",
    "MessageError",
    "SendMessageInput",
    "StartVerificationInput",
    "Template",
    "TemplateHeader",
    "TemplateHeaderInput",
    "TemplateIssue",
    "TemplateList",
    "TemplateValidation",
    "TemplateVariable",
    "TemplateVariableInput",
    "TextHeader",
    "TextHeaderInput",
    "UpdateTemplateInput",
    "Verification",
    "VerificationCheck",
]

# import apis into sdk package
from msgeasy._generated.api.media_api import MediaApi as MediaApi
from msgeasy._generated.api.messages_api import MessagesApi as MessagesApi
from msgeasy._generated.api.templates_api import TemplatesApi as TemplatesApi
from msgeasy._generated.api.verify_api import VerifyApi as VerifyApi

# import ApiClient
from msgeasy._generated.api_response import ApiResponse as ApiResponse
from msgeasy._generated.api_client import ApiClient as ApiClient
from msgeasy._generated.configuration import Configuration as Configuration
from msgeasy._generated.exceptions import OpenApiException as OpenApiException
from msgeasy._generated.exceptions import ApiTypeError as ApiTypeError
from msgeasy._generated.exceptions import ApiValueError as ApiValueError
from msgeasy._generated.exceptions import ApiKeyError as ApiKeyError
from msgeasy._generated.exceptions import ApiAttributeError as ApiAttributeError
from msgeasy._generated.exceptions import ApiException as ApiException

# import models into sdk package
from msgeasy._generated.models.api_error import ApiError as ApiError
from msgeasy._generated.models.check_verification_input import CheckVerificationInput as CheckVerificationInput
from msgeasy._generated.models.create_template_input import CreateTemplateInput as CreateTemplateInput
from msgeasy._generated.models.media import Media as Media
from msgeasy._generated.models.media_header import MediaHeader as MediaHeader
from msgeasy._generated.models.media_header_input import MediaHeaderInput as MediaHeaderInput
from msgeasy._generated.models.message import Message as Message
from msgeasy._generated.models.message_error import MessageError as MessageError
from msgeasy._generated.models.send_message_input import SendMessageInput as SendMessageInput
from msgeasy._generated.models.start_verification_input import StartVerificationInput as StartVerificationInput
from msgeasy._generated.models.template import Template as Template
from msgeasy._generated.models.template_header import TemplateHeader as TemplateHeader
from msgeasy._generated.models.template_header_input import TemplateHeaderInput as TemplateHeaderInput
from msgeasy._generated.models.template_issue import TemplateIssue as TemplateIssue
from msgeasy._generated.models.template_list import TemplateList as TemplateList
from msgeasy._generated.models.template_validation import TemplateValidation as TemplateValidation
from msgeasy._generated.models.template_variable import TemplateVariable as TemplateVariable
from msgeasy._generated.models.template_variable_input import TemplateVariableInput as TemplateVariableInput
from msgeasy._generated.models.text_header import TextHeader as TextHeader
from msgeasy._generated.models.text_header_input import TextHeaderInput as TextHeaderInput
from msgeasy._generated.models.update_template_input import UpdateTemplateInput as UpdateTemplateInput
from msgeasy._generated.models.verification import Verification as Verification
from msgeasy._generated.models.verification_check import VerificationCheck as VerificationCheck

