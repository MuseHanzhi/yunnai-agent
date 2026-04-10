from mcp.client.session import ClientSession
from mcp.types import Tool
from typing import (
    TypedDict,
    Any,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from .mcp_client import MCPClient

class ClientInfo(TypedDict):
    name: str
    version: str

class MCPInfo(TypedDict):
    name: str
    session: ClientSession | None
    client: "MCPClient"

class GetToolResult(TypedDict):
    message: str
    is_error: bool
    tools: list[Tool]

class CallResult(TypedDict):
    message: str
    is_error: bool
    content: Any
