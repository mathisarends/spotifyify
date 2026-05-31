from typing import Any

from pydantic import BaseModel, ConfigDict

type JsonPayload = BaseModel | dict[str, Any] | list[Any] | str | None
type SerializedJsonPayload = dict[str, Any] | list[Any] | str | None


class QueryParams(BaseModel):
    model_config = ConfigDict(extra="allow")


def dump_params(
    params: QueryParams | BaseModel | dict[str, Any] | None,
) -> dict[str, Any] | None:
    if params is None:
        return None
    if isinstance(params, BaseModel):
        return params.model_dump(mode="json", exclude_none=True)
    return QueryParams.model_validate(params).model_dump(mode="json", exclude_none=True)


def dump_payload(payload: JsonPayload) -> SerializedJsonPayload:
    if isinstance(payload, BaseModel):
        return payload.model_dump(mode="json", exclude_none=True)
    return payload
