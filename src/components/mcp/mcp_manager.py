from typing import Any
import asyncio

from mcp.types import Tool

from .mcp_client import MCPClient
from src.components.app_config.types import MCPOption
from src.components.logger.logger import LogCreator
from .types import (
    ClientInfo,
    MCPInfo,
    CallResult,
    GetToolResult
)


logger = LogCreator().instance.create(__name__)
class MCPManager:
    def __init__(self):
        self.mcp_servers: list[dict[str, str]] = []
        self.mcp_infos: dict[str, MCPInfo] = {}
        self.tools: dict[str, list[Tool]] = {}

    def is_activate(self, mcp_name: str):
        mcp_info = self.mcp_infos.get(mcp_name)
        if not mcp_info:
            return False
        return mcp_info["session"] is not None

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
            logger.info(f"'{mcp_name}'加载完成")
    
    async def activate(self, mcp_name: str) -> GetToolResult:
        """
        激活MCP，激活成功后返回该MCP的工具列表
        """
        if mcp_name not in self.mcp_infos:
            raise ValueError(f"MCP Server '{mcp_name}'不存在或者未开启")
        
        mcp_info = self.mcp_infos[mcp_name]
        client = mcp_info["client"]
        session = mcp_info.get("session")

        if session:
            tools = await session.list_tools()
            return {
                "message": "OK",
                "is_error": False,
                "tools": tools.tools
            }

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
        self.tools[mcp_name] = tools
        return {
            "message": "OK",
            "is_error": False,
            "tools": tools
        }
    
    def deactivate(self, mcp_name: str):
        mcp_info = self.mcp_infos[mcp_name]
        mcp_info["client"].disconnect()
    
    async def call_tool(self, mcp_name: str, tool_name: str, arguments: dict[str, Any] | None = None) -> CallResult:
        logger.info(f"调用MCP '{mcp_name}' 工具 '{tool_name}' 参数 '{arguments}'")
        session = self.mcp_infos[mcp_name]["session"]
        if not session:
            return {
                "message": f"MCP '{mcp_name}' 未激活",
                "is_error": True,
                "content": None
            }
        try:
            call_result = await session.call_tool(tool_name, arguments)
            logger.info(f"调用MCP '{mcp_name}' 工具 '{tool_name}' 结果 '{ 'ERROR' if call_result.isError else 'OK' }'")
            return {
                "message": "OK",
                "is_error": call_result.isError,
                "content": call_result.content
            }
        except Exception as ex:
            logger.error(f"调用MCP '{mcp_name}' 错误: {ex}", exc_info=ex)
            return {
                "message": "ERROR",
                "is_error": True,
                "content": None
            }

    async def get_mcp_session(self, mcp_name: str):
        session = self.mcp_infos[mcp_name]["session"]
        if not session:
            return ConnectionError(f"MCP '{mcp_name}' 未激活")
        return session
