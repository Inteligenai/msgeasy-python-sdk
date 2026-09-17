# coding: utf-8

"""MsgEasy WhatsApp API"""  # noqa: E501


from __future__ import annotations
import pprint
import re  # noqa: F401
import json

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator
from typing import Any, ClassVar, Dict, List, Optional
from typing_extensions import Annotated
from msgeasy._generated.models.template_variable_input import TemplateVariableInput
from typing import Optional, Set
from typing_extensions import Self
from pydantic_core import to_jsonable_python

class TextHeaderInput(BaseModel):
    """
    TextHeaderInput
    """ # noqa: E501
    type: StrictStr
    text: Annotated[str, Field(min_length=1, strict=True, max_length=60)]
    variables: Optional[List[TemplateVariableInput]] = None
    __properties: ClassVar[List[str]] = ["type", "text", "variables"]

    @field_validator('type')
    def type_validate_enum(cls, value):
        """Validates the enum"""
        if value not in set(['TEXT']):
            raise ValueError("must be one of enum values ('TEXT')")
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
        """Create an instance of TextHeaderInput from a JSON string"""
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
        # override the default output from pydantic by calling `to_dict()` of each item in variables (list)
        _items = []
        if self.variables:
            for _item_variables in self.variables:
                _items.append(_item_variables.to_dict() if _item_variables is not None else None)
            _dict['variables'] = _items
        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of TextHeaderInput from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "type": obj.get("type"),
            "text": obj.get("text"),
            "variables": [TemplateVariableInput.from_dict(_item) for _item in obj["variables"]] if obj.get("variables") is not None else None
        })
        return _obj


