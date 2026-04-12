import asyncio
from typing import (
    TYPE_CHECKING,
    Any
)

from src.types.message import MessageOptions

if TYPE_CHECKING:
    from src.application import Application

class IPCHandler:
    def __init__(self, app: "Application"):
        self.app = app
        self.ipc = app.ipc
        self.event_loop: None | asyncio.AbstractEventLoop = None
    
    def init(self):
        # self.ipc.handle("get-plugins", self.get_plugins)
        # self.ipc.handle("set-plugin", self.set_plugin)
        # self.ipc.handle("ready", self.ready_handler)

        self.ipc.on('send-msg', self.send_msg)
        self.ipc.on('client-ready', self._client_ready)
        self.ipc.on('close-app', self.close_app)

        self.event_loop = asyncio.get_event_loop()
    
    def close_app(self, params: dict):
        self.app.exit()
    
    def _client_ready(self, params: dict):
        # self._init_ai_chat(params)
        ...
    
    def send_msg(self, params: Any):
        message: MessageOptions = params
        text: str | None = message["data"]["text"]
        
        model_name = message["options"]["model_name"]

        # if self.event_loop and message:
            # c = self.app.sync_send_message({ 'role': 'user', 'content': text })
            # self.event_loop.create_task(c)
    
    # def set_plugin(self, params: dict):
    #     name: str = params.get("name", "")
    #     state: bool = params.get("state", False)
    #     try:
    #         self.app.plugin_manager.set_plugin_state(name, state)
    #         return True
    #     except ValueError as err:
    #         raise err
    
    # def ready_handler(self, params: dict):
    #     return self.app.is_ready
    
    # def get_plugins(self, params: dict):
    #     plugins: list[dict] = []
    #     for n, p in self.app.plugin_manager.plugins.items():
    #         plugins.append({
    #             "name": n,
    #             "desc": p.desc,
    #             "version": p.version,
    #             "state": p.state
    #         })
    #     return plugins
