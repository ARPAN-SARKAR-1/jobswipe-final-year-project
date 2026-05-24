from typing import Annotated

from fastapi import Query

PageQuery = Annotated[int, Query(ge=1)]
LimitQuery = Annotated[int, Query(ge=1, le=100)]


def pagination_offset(page: int, limit: int) -> int:
    return (page - 1) * limit
