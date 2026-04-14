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
        self.event_loop: asyncio.AbstractEventLoop = app.event_loop
    
    def init(self):
        self.ipc.on('send-msg', self.send_msg)
        self.ipc.on('close-app', self.close_app)

        self.event_loop = asyncio.get_event_loop()
    
    def close_app(self, params: dict):
        self.app.exit()
    
    def send_msg(self, params: Any):
        message: MessageOptions = params
        text: str | None = message["data"]["text"]
        model_name = message["options"]["model_name"]
        