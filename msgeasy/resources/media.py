"""Uploading a file for a send."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple, Union

from msgeasy._generated.api.media_api import MediaApi
from msgeasy._generated.models.media import Media
from msgeasy._transport import Transport

File = Union[str, "os.PathLike[str]", bytes]


class MediaResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._api = MediaApi(transport.api_client)

    def upload(
        self,
        file: File,
        *,
        filename: Optional[str] = None,
        timeout: Optional[float] = None,
        idempotency_key: Optional[str] = None,
    ) -> Media:
        """
        Uploads a file and returns it with the `med_` id to send with. Bytes need a
        `filename`, whose extension names the type.
        """
        return self._transport.call(
            self._api.media_upload_with_http_info,
            file=_part(file, filename),
            idempotent=True,
            timeout=timeout,
            idempotency_key=idempotency_key,
        )


def _part(file: File, filename: Optional[str]) -> Tuple[str, bytes]:
    if isinstance(file, bytes):
        if not filename:
            raise ValueError("filename is required when uploading bytes")
        return filename, file

    path = Path(file)
    return filename or path.name, path.read_bytes()
