# coding: utf-8

"""MsgEasy WhatsApp API"""  # noqa: E501


from __future__ import annotations
import pprint
import re  # noqa: F401
import json

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator
from typing import Any, ClassVar, Dict, List, Optional
from typing_extensions import Annotated
from typing import Optional, Set
from typing_extensions import Self
from pydantic_core import to_jsonable_python

class SendMessageInput(BaseModel):
    """
    SendMessageInput
    """ # noqa: E501
    to: Annotated[str, Field(strict=True)] = Field(description="The recipient's phone number in E.164 format.", json_schema_extra={"examples": ["+919812345678"]})
    type: StrictStr = Field(description="`text` only works inside the 24-hour window. `template` works any time but must be approved by Meta. `media` sends a file you uploaded first.")
    text: Optional[Annotated[str, Field(min_length=1, strict=True, max_length=4096)]] = Field(default=None, description="The message body. Required when `type` is `text`.", json_schema_extra={"examples": ["Your order has shipped."]})
    template_id: Optional[StrictStr] = Field(default=None, description="From `GET /v1/templates`. Required when `type` is `template`.", alias="templateId", json_schema_extra={"examples": ["tpl_3b9f1c2d4e5a6b7c8d9e0f1a2b3c4d5e"]})
    variables: Optional[Dict[str, StrictStr]] = Field(default=None, description="Template placeholder values, keyed by name or index. Omit one and the template's own example value is sent instead. Template messages only.", json_schema_extra={"examples": [{"1": "Asha", "2": "ORD-4471"}]})
    media_id: Optional[StrictStr] = Field(default=None, description="From `POST /v1/media/`. Required when `type` is `media`.", alias="mediaId", json_schema_extra={"examples": ["med_7c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f"]})
    caption: Optional[Annotated[str, Field(strict=True, max_length=1024)]] = Field(default=None, description="Text shown with the file. Media messages only.")
    reply_to: Optional[StrictStr] = Field(default=None, description="A `msg_` id or a WhatsApp id to quote, threading this as a reply.", alias="replyTo")
    __properties: ClassVar[List[str]] = ["to", "type", "text", "templateId", "variables", "mediaId", "caption", "replyTo"]

    @field_validator('to', mode="before")
    def to_validate_regular_expression(cls, value):
        """Validates the regular expression"""
        if isinstance(value, str) and not re.match(r"^\+[1-9]\d{6,14}$", value):
            raise ValueError(r"must validate the regular expression /^\+[1-9]\d{6,14}$/")
        return value

    @field_validator('type')
    def type_validate_enum(cls, value):
        """Validates the enum"""
        if value not in set(['template', 'text', 'media']):
            raise ValueError("must be one of enum values ('template', 'text', 'media')")
        return value

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
        """Create an instance of SendMessageInput from a JSON string"""
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
        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of SendMessageInput from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "to": obj.get("to"),
            "type": obj.get("type"),
            "text": obj.get("text"),
            "templateId": obj.get("templateId"),
            "variables": obj.get("variables"),
            "mediaId": obj.get("mediaId"),
            "caption": obj.get("caption"),
            "replyTo": obj.get("replyTo")
        })
        return _obj


