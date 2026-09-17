"""Cursor paging, identical on every `/v1` list. A caller never sees a cursor."""

from __future__ import annotations

from typing import Any, Callable, Iterator, Optional

#: Given a cursor, returns a page carrying `data` and `has_more`.
Fetch = Callable[[Optional[str]], Any]


def paginate(fetch: Fetch) -> Iterator[Any]:
    """Yields every item across pages, stopping when the API says there are no more."""
    cursor: Optional[str] = None
    while True:
        page = fetch(cursor)
        yield from page.data
        # The empty check is not redundant: a page claiming `has_more` while
        # carrying nothing would otherwise loop on the same cursor for ever.
        if not page.has_more or not page.data:
            return
        cursor = page.data[-1].id
