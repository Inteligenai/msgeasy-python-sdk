# coding: utf-8

"""MsgEasy WhatsApp API"""  # noqa: E501


from __future__ import annotations
import pprint
import re  # noqa: F401
import json

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator
from typing import Any, ClassVar, Dict, List, Optional
from typing_extensions import Annotated
from msgeasy._generated.models.template_header_input import TemplateHeaderInput
from msgeasy._generated.models.template_variable_input import TemplateVariableInput
from typing import Optional, Set
from typing_extensions import Self
from pydantic_core import to_jsonable_python

class UpdateTemplateInput(BaseModel):
    """
    UpdateTemplateInput
    """ # noqa: E501
    name: Optional[Annotated[str, Field(strict=True)]] = Field(default=None, description="Lowercase letters, digits and underscores. Claimed permanently at Meta — a deleted name stays reserved for about 30 days.", json_schema_extra={"examples": ["order_shipped"]})
    category: Optional[StrictStr] = Field(default=None, description="Utility only. Marketing templates can be listed and sent, but not created here.")
    language: Optional[Annotated[str, Field(min_length=2, strict=True, max_length=10)]] = Field(default=None, description="Meta's language code, not ours.", json_schema_extra={"examples": ["en_US"]})
    body: Optional[Annotated[str, Field(min_length=1, strict=True, max_length=1024)]] = Field(default=None, description="The message text. Use `{{1}}`, `{{2}}` for placeholders.", json_schema_extra={"examples": ["Hi {{1}}, your order {{2}} has shipped."]})
    variables: Optional[List[TemplateVariableInput]] = Field(default=None, description="An example value per placeholder. Meta rejects a template whose examples are missing.")
    header: Optional[TemplateHeaderInput] = Field(default=None, description="A text or media header. Omit it entirely for no header.")
    footer: Optional[Annotated[str, Field(strict=True, max_length=60)]] = Field(default=None, description="Small text under the body.")
    __properties: ClassVar[List[str]] = ["name", "category", "language", "body", "variables", "header", "footer"]

    @field_validator('name', mode="before")
    def name_validate_regular_expression(cls, value):
        """Validates the regular expression"""
        if value is None:
            return value

        if isinstance(value, str) and not re.match(r"^[a-z0-9_]{1,512}$", value):
            raise ValueError(r"must validate the regular expression /^[a-z0-9_]{1,512}$/")
        return value

    @field_validator('category')
    def category_validate_enum(cls, value):
        """Validates the enum"""
        if value is None:
            return value

        if value not in set(['UTILITY']):
            raise ValueError("must be one of enum values ('UTILITY')")
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
        """Create an instance of UpdateTemplateInput from a JSON string"""
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
        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of UpdateTemplateInput from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "name": obj.get("name"),
            "category": obj.get("category"),
            "language": obj.get("language"),
            "body": obj.get("body"),
            "variables": [TemplateVariableInput.from_dict(_item) for _item in obj["variables"]] if obj.get("variables") is not None else None,
            "header": TemplateHeaderInput.from_dict(obj["header"]) if obj.get("header") is not None else None,
            "footer": obj.get("footer")
        })
        return _obj


