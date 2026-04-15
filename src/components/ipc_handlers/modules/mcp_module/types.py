from typing import TypedDict, Any

class ActivateMCPHandlerParams(TypedDict):
    mcp_name: str


class GetToolsParams(TypedDict):
    mcp_name: str
    auto_activate: bool

class GetAllToolsParams(TypedDict):
    auto_activate: bool

class CallToolParams(TypedDict):
    mcp_name: str
    tool_name: str
    arguments: dict[str, Any] | None

class ResourcesParams(TypedDict):
    mcp_name: str
    cursor: str | None