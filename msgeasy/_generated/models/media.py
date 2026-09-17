# coding: utf-8

"""MsgEasy WhatsApp API"""  # noqa: E501


from __future__ import annotations
import pprint
import re  # noqa: F401
import json

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, StrictStr
from typing import Any, ClassVar, Dict, List, Optional
from typing_extensions import Annotated
from typing import Optional, Set
from typing_extensions import Self
from pydantic_core import to_jsonable_python

class Media(BaseModel):
    """
    Media
    """ # noqa: E501
    id: StrictStr = Field(description="Pass this to `POST /v1/messages` as `mediaId`.", json_schema_extra={"examples": ["med_7c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f"]})
    filename: Optional[StrictStr] = Field(description="The name the file was uploaded under.", json_schema_extra={"examples": ["invoice.pdf"]})
    mime_type: Optional[StrictStr] = Field(description="The type we normalised to, which may differ from the one you declared.", alias="mimeType", json_schema_extra={"examples": ["application/pdf"]})
    size_bytes: Optional[Annotated[int, Field(le=9007199254740991, strict=True, ge=-9007199254740991)]] = Field(description="Size of the stored file.", alias="sizeBytes")
    created_at: datetime = Field(description="When the file was uploaded.", alias="createdAt")
    __properties: ClassVar[List[str]] = ["id", "filename", "mimeType", "sizeBytes", "createdAt"]

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
        """Create an instance of Media from a JSON string"""
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
        # set to None if filename (nullable) is None
        # and model_fields_set contains the field
        if self.filename is None and "filename" in self.model_fields_set:
            _dict['filename'] = None

        # set to None if mime_type (nullable) is None
        # and model_fields_set contains the field
        if self.mime_type is None and "mime_type" in self.model_fields_set:
            _dict['mimeType'] = None

        # set to None if size_bytes (nullable) is None
        # and model_fields_set contains the field
        if self.size_bytes is None and "size_bytes" in self.model_fields_set:
            _dict['sizeBytes'] = None

        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of Media from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "id": obj.get("id"),
            "filename": obj.get("filename"),
            "mimeType": obj.get("mimeType"),
            "sizeBytes": obj.get("sizeBytes"),
            "createdAt": obj.get("createdAt")
        })
        return _obj


