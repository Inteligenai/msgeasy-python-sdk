"""Utility templates: the only message kind sendable outside the 24-hour window."""

from __future__ import annotations

from typing import Any, Iterator, List, Optional

from msgeasy._generated.api.templates_api import TemplatesApi
from msgeasy._generated.models.create_template_input import CreateTemplateInput
from msgeasy._generated.models.template import Template
from msgeasy._generated.models.template_header_input import TemplateHeaderInput
from msgeasy._generated.models.template_list import TemplateList
from msgeasy._generated.models.template_validation import TemplateValidation
from msgeasy._generated.models.template_variable_input import (
    TemplateVariableInput,
)
from msgeasy._generated.models.update_template_input import UpdateTemplateInput
from msgeasy._pagination import paginate
from msgeasy._transport import Transport


def _definition(
    name: str,
    category: str,
    language: str,
    body: str,
    variables: Optional[List[TemplateVariableInput]],
    header: Optional[TemplateHeaderInput],
    footer: Optional[str],
) -> CreateTemplateInput:
    """`create` and `validate` take the same definition; only what happens to it
    differs."""
    return CreateTemplateInput(
        name=name,
        category=category,
        language=language,
        body=body,
        variables=variables,
        header=header,
        footer=footer,
    )


class TemplatesResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._api = TemplatesApi(transport.api_client)

    def list(
        self,
        *,
        status: Optional[str] = None,
        updated_after: Optional[Any] = None,
        limit: Optional[int] = None,
        starting_after: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> TemplateList:
        """
        Reads one page. `has_more` says whether another exists; pass the last
        `id` in `data` as `starting_after` to fetch it.
        """
        return self._page(
            status=status,
            updated_after=updated_after,
            limit=limit,
            starting_after=starting_after,
            timeout=timeout,
        )

    def list_all(
        self,
        *,
        status: Optional[str] = None,
        updated_after: Optional[Any] = None,
        limit: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> Iterator[Template]:
        """
        Iterates every template, paging as it goes. `limit` sizes each page, not
        the total.
        """
        return paginate(
            lambda cursor: self._page(
                status=status,
                updated_after=updated_after,
                limit=limit,
                starting_after=cursor,
                timeout=timeout,
            )
        )

    def _page(
        self,
        *,
        status: Optional[str],
        updated_after: Optional[Any],
        limit: Optional[int],
        starting_after: Optional[str],
        timeout: Optional[float],
    ) -> TemplateList:
        return self._transport.call(
            self._api.templates_list_with_http_info,
            limit=limit,
            starting_after=starting_after,
            status=status,
            updated_after=updated_after,
            idempotent=False,
            timeout=timeout,
        )

    def get(self, template_id: str, *, timeout: Optional[float] = None) -> Template:
        """Reads one template, including why Meta rejected it if it did."""
        return self._transport.call(
            self._api.templates_get_with_http_info,
            id=template_id,
            idempotent=False,
            timeout=timeout,
        )

    def create(
        self,
        *,
        name: str,
        category: str,
        language: str,
        body: str,
        variables: Optional[List[TemplateVariableInput]] = None,
        header: Optional[TemplateHeaderInput] = None,
        footer: Optional[str] = None,
        timeout: Optional[float] = None,
        idempotency_key: Optional[str] = None,
    ) -> Template:
        """
        Creates a template and submits it to Meta in one call. Returns
        "processing"; poll `get` until approved or rejected.
        """
        return self._transport.call(
            self._api.templates_create_with_http_info,
            create_template_input=_definition(
                name, category, language, body, variables, header, footer
            ),
            idempotent=True,
            timeout=timeout,
            idempotency_key=idempotency_key,
        )

    def update(
        self,
        template_id: str,
        *,
        name: Optional[str] = None,
        category: Optional[str] = None,
        language: Optional[str] = None,
        body: Optional[str] = None,
        variables: Optional[List[TemplateVariableInput]] = None,
        header: Optional[TemplateHeaderInput] = None,
        footer: Optional[str] = None,
        timeout: Optional[float] = None,
        idempotency_key: Optional[str] = None,
    ) -> Template:
        """
        Edits a template Meta has not frozen — one never submitted, or rejected.
        An approved or in-review one raises `TemplateError`.
        """
        return self._transport.call(
            self._api.templates_update_with_http_info,
            id=template_id,
            update_template_input=UpdateTemplateInput(
                name=name,
                category=category,
                language=language,
                body=body,
                variables=variables,
                header=header,
                footer=footer,
            ),
            idempotent=True,
            timeout=timeout,
            idempotency_key=idempotency_key,
        )

    def validate(
        self,
        *,
        name: str,
        category: str,
        language: str,
        body: str,
        variables: Optional[List[TemplateVariableInput]] = None,
        header: Optional[TemplateHeaderInput] = None,
        footer: Optional[str] = None,
        timeout: Optional[float] = None,
        idempotency_key: Optional[str] = None,
    ) -> TemplateValidation:
        """
        Checks a definition against the rules `create` enforces, without
        submitting it or claiming its name.
        """
        return self._transport.call(
            self._api.templates_validate_with_http_info,
            create_template_input=_definition(
                name, category, language, body, variables, header, footer
            ),
            idempotent=True,
            timeout=timeout,
            idempotency_key=idempotency_key,
        )
