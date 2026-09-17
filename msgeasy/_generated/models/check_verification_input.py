# coding: utf-8

"""MsgEasy WhatsApp API"""  # noqa: E501


from __future__ import annotations
import pprint
import re  # noqa: F401
import json

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Any, ClassVar, Dict, List
from typing_extensions import Annotated
from typing import Optional, Set
from typing_extensions import Self
from pydantic_core import to_jsonable_python

class CheckVerificationInput(BaseModel):
    """
    CheckVerificationInput
    """ # noqa: E501
    verification_id: Annotated[str, Field(min_length=1, strict=True)] = Field(description="The id returned by `/v1/verify/start`. The `vrf_` prefix is optional.", alias="verificationId", json_schema_extra={"examples": ["vrf_9f2c8d1e4b7a4c3f9e0d2a5b6c7d8e9f"]})
    code: Annotated[str, Field(strict=True)] = Field(description="The code the user entered. Digits only.", json_schema_extra={"examples": ["483920"]})
    __properties: ClassVar[List[str]] = ["verificationId", "code"]

    @field_validator('code', mode="before")
    def code_validate_regular_expression(cls, value):
        """Validates the regular expression"""
        if isinstance(value, str) and not re.match(r"^\d+$", value):
            raise ValueError(r"must validate the regular expression /^\d+$/")
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
        """Create an instance of CheckVerificationInput from a JSON string"""
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
        """Create an instance of CheckVerificationInput from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "verificationId": obj.get("verificationId"),
            "code": obj.get("code")
        })
        return _obj


