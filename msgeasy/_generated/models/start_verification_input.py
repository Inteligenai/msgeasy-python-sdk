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

class StartVerificationInput(BaseModel):
    """
    StartVerificationInput
    """ # noqa: E501
    phone: Annotated[str, Field(strict=True)] = Field(description="The recipient's phone number in E.164 format, including the country code.", json_schema_extra={"examples": ["+919812345678"]})
    channel: Optional[StrictStr] = Field(default='whatsapp', description="Delivery channel. WhatsApp is the only value today.")
    ttl_seconds: Optional[Annotated[int, Field(le=3600, strict=True, ge=60)]] = Field(default=None, description="How long the code stays valid. Defaults to the account's Verify setting.", alias="ttlSeconds", json_schema_extra={"examples": [300]})
    code_length: Optional[Annotated[int, Field(le=10, strict=True, ge=4)]] = Field(default=None, description="How many digits the code has. Defaults to the account's Verify setting.", alias="codeLength", json_schema_extra={"examples": [6]})
    __properties: ClassVar[List[str]] = ["phone", "channel", "ttlSeconds", "codeLength"]

    @field_validator('phone', mode="before")
    def phone_validate_regular_expression(cls, value):
        """Validates the regular expression"""
        if isinstance(value, str) and not re.match(r"^\+[1-9]\d{6,14}$", value):
            raise ValueError(r"must validate the regular expression /^\+[1-9]\d{6,14}$/")
        return value

    @field_validator('channel')
    def channel_validate_enum(cls, value):
        """Validates the enum"""
        if value is None:
            return value

        if value not in set(['whatsapp']):
            raise ValueError("must be one of enum values ('whatsapp')")
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
        """Create an instance of StartVerificationInput from a JSON string"""
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
        """Create an instance of StartVerificationInput from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "phone": obj.get("phone"),
            "channel": obj.get("channel") if obj.get("channel") is not None else 'whatsapp',
            "ttlSeconds": obj.get("ttlSeconds"),
            "codeLength": obj.get("codeLength")
        })
        return _obj


