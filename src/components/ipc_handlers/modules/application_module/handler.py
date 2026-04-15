import asyncio

from typing import (
    TYPE_CHECKING,
    Any
)
from .types import *

if TYPE_CHECKING:
    from src.application import Application

class Handler:
    def __init__(self, app: "Application"):
        self.app = app
        self.ipc = app.ipc
        self.event_loop: asyncio.AbstractEventLoop = app.event_loop
        self.init()
    
    def init(self):
        self.ipc.on('send-msg', self.send_msg)
        self.ipc.on('close-app', self.close_app)
    
    def close_app(self, params: dict):
        self.app.exit()
    
    def send_msg(self, params: Any):
        message: MessageOptions = params
        text: str | None = message["data"]["text"]
        self.event_loop.create_task(self.app.send_message(text))
