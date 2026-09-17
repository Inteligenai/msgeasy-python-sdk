# coding: utf-8

"""MsgEasy WhatsApp API"""  # noqa: E501


from __future__ import annotations
import pprint
import re  # noqa: F401
import json

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, field_validator
from typing import Any, ClassVar, Dict, List, Literal, Optional, Union
from msgeasy._generated.models.message_error import MessageError
from typing import Optional, Set
from typing_extensions import Self
from pydantic_core import to_jsonable_python

class Message(BaseModel):
    """
    Message
    """ # noqa: E501
    id: StrictStr = Field(description="Pass this to `GET /v1/messages/{id}` for delivery status.", json_schema_extra={"examples": ["msg_7726793e1a4b4c8d9e0f1a2b3c4d5e6f"]})
    status: Union[Literal['accepted', 'sent', 'delivered', 'read', 'failed'], StrictStr] = Field(description="`accepted` means we have it, not that it arrived. It moves to `sent`, `delivered` and `read` as WhatsApp reports back, or to `failed`.")
    to: StrictStr = Field(description="The recipient, echoed back.")
    type: Union[Literal['template', 'text', 'media'], StrictStr] = Field(description="The kind of message that was sent.")
    whatsapp_message_id: Optional[StrictStr] = Field(description="Meta's own id, for correlating in WhatsApp Manager. Null on a `test` key.", alias="whatsappMessageId")
    error: Optional[MessageError]
    created_at: datetime = Field(description="When we accepted the message.", alias="createdAt")
    test_mode: Optional[StrictBool] = Field(default=None, description="Present and `true` on a `test` key. Nothing reached WhatsApp.", alias="testMode")
    __properties: ClassVar[List[str]] = ["id", "status", "to", "type", "whatsappMessageId", "error", "createdAt", "testMode"]



    model_config = ConfigDict(
        validate_by_name=True,
        validate_by_alias=True,
        validate_assignment=True,
        protected_namespaces=(),
    )


    def to_str(self) -> str:
        """Returns the string representation of the model using alias"""
        return pprint.pformat(self.model_dump(by_alias=True))

    def to_json(self) -> str:
        """Returns the JSON representation of the model using alias"""
        return json.dumps(to_jsonable_python(self.to_dict()))

    @classmethod
    def from_json(cls, json_str: str) -> Optional[Self]:
        """Create an instance of Message from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self) -> Dict[str, Any]:
        """Return the dictionary representation of the model using alias.

        This has the following differences from calling pydantic's
        `self.model_dump(by_alias=True)`:

        * `None` is only added to the output dict for nullable fields that
          were set at model initialization. Other fields with value `None`
          are ignored.
        """
        excluded_fields: Set[str] = set([
        ])

        _dict = self.model_dump(
            by_alias=True,
            exclude=excluded_fields,
            exclude_none=True,
        )
        # override the default output from pydantic by calling `to_dict()` of error
        if self.error:
            _dict['error'] = self.error.to_dict()
        # set to None if whatsapp_message_id (nullable) is None
        # and model_fields_set contains the field
        if self.whatsapp_message_id is None and "whatsapp_message_id" in self.model_fields_set:
            _dict['whatsappMessageId'] = None

        # set to None if error (nullable) is None
        # and model_fields_set contains the field
        if self.error is None and "error" in self.model_fields_set:
            _dict['error'] = None

        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of Message from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "id": obj.get("id"),
            "status": obj.get("status"),
            "to": obj.get("to"),
            "type": obj.get("type"),
            "whatsappMessageId": obj.get("whatsappMessageId"),
            "error": MessageError.from_dict(obj["error"]) if obj.get("error") is not None else None,
            "createdAt": obj.get("createdAt"),
            "testMode": obj.get("testMode")
        })
        return _obj


