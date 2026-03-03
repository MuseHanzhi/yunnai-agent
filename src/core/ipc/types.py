from typing import (
    NotRequired,
    Required,
    TypedDict,
    Literal,
    Any
)

class IPCData(TypedDict):
    id: NotRequired[str]
    name: Required[str]
    type: Required[Literal["event", "invoke-res", "invoke-req"]]

class IPCCommand(IPCData):
    arguments: dict[str, Any]

class IPCInvokeResult(IPCData):
    data: Any
    exceptMessage: NotRequired[str] | None
