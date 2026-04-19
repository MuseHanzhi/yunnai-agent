import asyncio
from typing import (
    TYPE_CHECKING
)

from ..ipc.ipc import IPCServer
from .modules.mcp_module.handler import Handler as MCPHandler
from .modules.application_module.handler import Handler as AppHandler

if TYPE_CHECKING:
    from src.application import Application

class IPCHandler:
    def __init__(self, app: "Application", ipc: IPCServer):
        self.app = app
        self.event_loop: asyncio.AbstractEventLoop = app.event_loop
        self.mcp_module: None | MCPHandler = None
        self.app_module = AppHandler(self.app, ipc)
        self.ipc = ipc
    
    def init(self):
        if self.app.mcp_manager:
            self.mcp_module = MCPHandler(self.app.mcp_manager, self.ipc)
        self.event_loop = asyncio.get_event_loop()
