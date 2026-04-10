from typing import Any
import asyncio

from mcp.types import TextContent

from .mcp_client import MCPClient
from src.components.app_config.types import MCPOption
from .types import (
    ClientInfo,
    MCPInfo,
    CallResult,
    GetToolResult
)

class MCPManager:
    def __init__(self):
        self.mcp_servers: list[dict[str, str]] = []
        self.mcp_infos: dict[str, MCPInfo] = {}

    def load(self, mcp_option: MCPOption, client_info: ClientInfo):
        servers = mcp_option.get("servers")
        for mcp_name in servers if servers else []:
            if servers is None or not servers[mcp_name].get("enable"):
                continue
            mcp_server = servers[mcp_name]
            self.mcp_infos[mcp_name] = {
                "name": mcp_name,
                "session": None,
                "client": MCPClient(client_info, mcp_server)
            }
            self.mcp_servers.append({
                "name": mcp_name,
                "desc": mcp_server["desc"]
            })
    
    async def activate(self, mcp_name: str) -> GetToolResult:
        if mcp_name not in self.mcp_infos:
            raise ValueError(f"MCP Server '{mcp_name}'不存在或者未开启")
        mcp_info = self.mcp_infos[mcp_name]
        client = mcp_info["client"]
        event_loop = asyncio.get_running_loop()
        future = asyncio.Future()

        def on_connected():
            future.set_result(None)
            client.on_connect_error = None
            client.on_connected = None
        
        def on_connect_error(ex: Exception):
            future.set_exception(ex)
            client.on_connect_error = None
            client.on_connected = None

        client.on_connected = on_connected
        client.on_connect_error = on_connect_error
        event_loop.create_task(client.connect())
        try:
            await future
        except Exception as ex:
            raise ex
        session = client.get_session()
        self.mcp_infos[mcp_name]["session"] = session
        tools = (await session.list_tools()).model_dump()["tools"]
        return {
            "message": "OK",
            "is_error": False,
            "tools": tools
        }
    
    def deactivate(self, mcp_name: str):
        mcp_info = self.mcp_infos[mcp_name]
        mcp_info["client"].disconnect()
    
    async def call_tool(self, mcp_name: str, tool_name: str, arguments: dict[str, Any] | None = None) -> CallResult:
        session = self.mcp_infos[mcp_name]["session"]
        if not session:
            return {
                "message": f"MCP '{mcp_name}' 未激活",
                "is_error": True,
                "content": None
            }
        call_result = await session.call_tool(tool_name, arguments)
        return {
            "message": "OK",
            "is_error": call_result.isError,
            "content": call_result.content
        }

    async def get_mcp_session(self, mcp_name: str):
        session = self.mcp_infos[mcp_name]["session"]
        if not session:
            return ConnectionError(f"MCP '{mcp_name}' 未激活")
        return session
