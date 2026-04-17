from asyncio import AbstractEventLoop
from os import path
from openai.types.chat import ChatCompletion, ChatCompletionChunk
import yaml

from src.components.ai_chat.chat_state import ChatState
from src.plugins.plugin import Plugin
from src.components.logger.logger import LogCreator

from .types import *
from .ipc.ipc import IPCServer
from .ipc_handlers.ipc_handler import IPCHandler

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.application import Application


logger = LogCreator.instance.create(__name__)
class IPCPlugin(Plugin):
    app: "Application"
    event_loop: AbstractEventLoop
    handler: IPCHandler
    def __init__(self):
        super().__init__("ipc_plugin")
        self.config: IPCOption = self.load_config()
        self.ipc = IPCServer(f"{self.config["protocol"]}://{self.config['host']}:{self.config['port']}")
        self.hook_registry = [
            "on_app_before_initialize",
            "on_app_will_close",
            "on_ready",
            "on_llm_response",
            "on_message_after_sended"
        ]
    
    def load_config(self):
        config_path = path.join(path.dirname(__file__), "config.yaml")
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    def on_app_before_initialize(self, app: "Application", event_loop: AbstractEventLoop):
        self.app = app
        self.event_loop = event_loop
        self.handler = IPCHandler(app, self.ipc)
    
    async def listen_ipc(self):
        logger.info("正在启动IPC服务")
        self.ipc.on_ipc_error = self.on_ipc_error
        self.ipc.on_ipc_ready = self.on_ipc_ready
        await self.ipc.start()
    
    def on_ipc_ready(self):
        logger.info("IPC服务启动成功，初始化IPC业务模块")
        self.handler.init()
        logger.info("IPC业务模块初始化完成")
    
    def on_ipc_error(self, error: Exception):
        logger.error(f"IPC服务启动失败: {error}")
        self.app.exit()

    def on_ready(self):
        self.event_loop.create_task(self.listen_ipc())
    
    def on_llm_response(self, chat_completion: ChatCompletionChunk | ChatCompletion):
        self.event_loop.create_task(self.ipc.emit("on_llm_response", completion=chat_completion.model_dump_json()))
    
    def on_app_will_close(self):
        self.event_loop.create_task(self.ipc.emit("on_app_will_close"))
    
    def on_message_after_sended(self, state: ChatState):
        self.event_loop.create_task(self.ipc.emit("on_message_after_sended"))
