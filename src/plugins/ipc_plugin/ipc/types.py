from typing import (
    TypedDict,
    Literal,
    Any
)

class Event(TypedDict):
    type: Literal['event']
    name: str
    arguments: dict[str, Any]

class InvokeRequest(TypedDict):
    id: str
    name: str
    type: Literal["invoke-req"]
    arguments: dict[str, Any]

class InvokeResponse(TypedDict):
    id: str
    name: str
    type: Literal["invoke-res"]
    data: Any
    exceptMessage: str | None


IPCData = Event | InvokeRequest | InvokeResponse
