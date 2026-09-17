# coding: utf-8

"""MsgEasy WhatsApp API"""  # noqa: E501


from __future__ import annotations
import pprint
import re  # noqa: F401
import json

from pydantic import BaseModel, ConfigDict, Field, StrictBool
from typing import Any, ClassVar, Dict, List
from msgeasy._generated.models.template_issue import TemplateIssue
from typing import Optional, Set
from typing_extensions import Self
from pydantic_core import to_jsonable_python

class TemplateValidation(BaseModel):
    """
    TemplateValidation
    """ # noqa: E501
    valid: StrictBool = Field(description="Whether the template would be accepted for submission.")
    issues: List[TemplateIssue] = Field(description="Every problem at once, so a template is fixable in one round trip. Empty when valid.")
    __properties: ClassVar[List[str]] = ["valid", "issues"]

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
        """Create an instance of TemplateValidation from a JSON string"""
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
        # override the default output from pydantic by calling `to_dict()` of each item in issues (list)
        _items = []
        if self.issues:
            for _item_issues in self.issues:
                _items.append(_item_issues.to_dict() if _item_issues is not None else None)
            _dict['issues'] = _items
        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of TemplateValidation from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "valid": obj.get("valid"),
            "issues": [TemplateIssue.from_dict(_item) for _item in obj["issues"]] if obj.get("issues") is not None else None
        })
        return _obj


