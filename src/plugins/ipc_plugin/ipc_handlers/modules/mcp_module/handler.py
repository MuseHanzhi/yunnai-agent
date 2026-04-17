from mcp.types import Tool, PaginatedRequestParams

from src.components.mcp.mcp_manager import MCPManager
from src.plugins.ipc_plugin.ipc.ipc import IPCServer

from.types import *

from typing import (
    Any
)

class Handler:
    def __init__(self, mcp_manager: MCPManager, ipc: IPCServer):
        self.mcp_manager = mcp_manager
        self.ipc = ipc
        self.init()
    
    def init(self):
        self.ipc.handle("activate-mcp", self.activate_mcp)
        self.ipc.handle("get-tools", self.get_tools)
        self.ipc.handle("get-mcp-list", self.get_mcp_list)
        self.ipc.handle("get-all-tools", self.get_all_tools)
        self.ipc.handle("call-tool", self.call_tool)
        self.ipc.handle("list-resources", self.list_resources)
        self.ipc.handle("deactivate-mcp", self.deactivate_mcp)
    
    def deactivate_mcp(self, params: Any):
        argument: ActivateMCPHandlerParams = params
        self.mcp_manager.deactivate(argument["mcp_name"])

    async def list_resources(self, params: Any):
        arguments: ResourcesParams = params
        try:
            session = self.mcp_manager.get_mcp_session(arguments["mcp_name"])
            return await session.list_resources(params=PaginatedRequestParams(cursor=arguments["cursor"]))
        except:
            raise


    async def call_tool(self, params: Any):
        arguments: CallToolParams = params
        return await self.mcp_manager.call_tool(arguments["mcp_name"], arguments["tool_name"], arguments["arguments"])

    async def get_all_tools(self, params: Any):
        arguments: GetAllToolsParams = params
        tools: dict[str, list[Tool]] = {}
        for mcp_item in self.mcp_manager.mcp_servers:
            if not self.mcp_manager.is_activate(mcp_item["name"]) and arguments["auto_activate"]:
                tools[mcp_item["name"]] = (await self.mcp_manager.activate(mcp_item["name"]))["tools"]
                continue
            tools[mcp_item["name"]] = self.mcp_manager.mcp_infos[mcp_item["name"]]["tools"]
        return tools
    async def get_mcp_list(self, _):
        return self.mcp_manager.mcp_servers
    async def get_tools(self, params: Any):
        arguments: GetToolsParams = params

        if not self.mcp_manager.is_activate(arguments["mcp_name"]):
            if not arguments["auto_activate"]:      # 不自动激活
                raise Exception("MCP is not activated")
            return await self.mcp_manager.activate(arguments["mcp_name"])

        # 激活后直接返回工具集
        return self.mcp_manager.mcp_infos[arguments["mcp_name"]]["tools"]
    
    async def activate_mcp(self, params: Any):
        argument: ActivateMCPHandlerParams = params
        return await self.mcp_manager.activate(argument["mcp_name"])