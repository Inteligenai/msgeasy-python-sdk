# coding: utf-8

"""MsgEasy WhatsApp API"""  # noqa: E501


from __future__ import annotations
import pprint
import re  # noqa: F401
import json

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator
from typing import Any, ClassVar, Dict, List, Literal, Optional, Union
from msgeasy._generated.models.template_header import TemplateHeader
from msgeasy._generated.models.template_variable import TemplateVariable
from typing import Optional, Set
from typing_extensions import Self
from pydantic_core import to_jsonable_python

class Template(BaseModel):
    """
    Template
    """ # noqa: E501
    id: StrictStr = Field(description="Pass this to `POST /v1/messages` as `templateId`.", json_schema_extra={"examples": ["tpl_3b9f1c2d4e5a6b7c8d9e0f1a2b3c4d5e"]})
    name: StrictStr = Field(description="The name this template holds at Meta.")
    status: Union[Literal['pending', 'processing', 'approved', 'rejected'], StrictStr] = Field(description="Only an `approved` template can be sent. `pending` and `processing` are waiting on Meta; `rejected` carries a `rejectionReason`.")
    category: Union[Literal['MARKETING', 'UTILITY'], StrictStr] = Field(description="Meta re-categorises on approval, so this can differ from what was submitted.")
    language: StrictStr = Field(description="Meta's language code.")
    body: StrictStr = Field(description="The message text, with `{{n}}` placeholders.")
    variables: List[TemplateVariable] = Field(description="One entry per placeholder in the body.")
    header: Optional[TemplateHeader] = Field(description="Null when the template has no header.")
    footer: Optional[StrictStr] = Field(description="Null when the template has no footer.")
    rejection_reason: Optional[StrictStr] = Field(description="Why Meta refused it. Null unless `status` is `rejected`.", alias="rejectionReason")
    approved_at: Optional[datetime] = Field(description="Null until Meta approves it.", alias="approvedAt")
    created_at: datetime = Field(description="When the template was created here.", alias="createdAt")
    updated_at: datetime = Field(description="Last change, including a status change from Meta.", alias="updatedAt")
    __properties: ClassVar[List[str]] = ["id", "name", "status", "category", "language", "body", "variables", "header", "footer", "rejectionReason", "approvedAt", "createdAt", "updatedAt"]



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
        """Create an instance of Template from a JSON string"""
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
        # override the default output from pydantic by calling `to_dict()` of header
        if self.header:
            _dict['header'] = self.header.to_dict()
        # set to None if header (nullable) is None
        # and model_fields_set contains the field
        if self.header is None and "header" in self.model_fields_set:
            _dict['header'] = None

        # set to None if footer (nullable) is None
        # and model_fields_set contains the field
        if self.footer is None and "footer" in self.model_fields_set:
            _dict['footer'] = None

        # set to None if rejection_reason (nullable) is None
        # and model_fields_set contains the field
        if self.rejection_reason is None and "rejection_reason" in self.model_fields_set:
            _dict['rejectionReason'] = None

        # set to None if approved_at (nullable) is None
        # and model_fields_set contains the field
        if self.approved_at is None and "approved_at" in self.model_fields_set:
            _dict['approvedAt'] = None

        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of Template from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "id": obj.get("id"),
            "name": obj.get("name"),
            "status": obj.get("status"),
            "category": obj.get("category"),
            "language": obj.get("language"),
            "body": obj.get("body"),
            "variables": [TemplateVariable.from_dict(_item) for _item in obj["variables"]] if obj.get("variables") is not None else None,
            "header": TemplateHeader.from_dict(obj["header"]) if obj.get("header") is not None else None,
            "footer": obj.get("footer"),
            "rejectionReason": obj.get("rejectionReason"),
            "approvedAt": obj.get("approvedAt"),
            "createdAt": obj.get("createdAt"),
            "updatedAt": obj.get("updatedAt")
        })
        return _obj


