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

class TemplateVariable(BaseModel):
    """
    TemplateVariable
    """ # noqa: E501
    index: Annotated[int, Field(le=9007199254740991, strict=True, ge=1)]
    example_value: StrictStr = Field(alias="exampleValue")
    param_name: Optional[Annotated[str, Field(strict=True)]] = Field(default=None, alias="paramName")
    __properties: ClassVar[List[str]] = ["index", "exampleValue", "paramName"]

    @field_validator('param_name', mode="before")
    def param_name_validate_regular_expression(cls, value):
        """Validates the regular expression"""
        if value is None:
            return value

        if isinstance(value, str) and not re.match(r"^[a-z0-9_]{1,60}$", value):
            raise ValueError(r"must validate the regular expression /^[a-z0-9_]{1,60}$/")
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
        """Create an instance of TemplateVariable from a JSON string"""
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
        """Create an instance of TemplateVariable from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "index": obj.get("index"),
            "exampleValue": obj.get("exampleValue"),
            "paramName": obj.get("paramName")
        })
        return _obj


