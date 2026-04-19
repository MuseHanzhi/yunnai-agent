# import inspect
from asyncio import AbstractEventLoop
import os

from openai.types.chat import ChatCompletionChunk, ChatCompletion

from src.components.ai_chat.chat_state import ChatState
from src.types.lfecycle_hooks import Hooks

from typing import (
    TYPE_CHECKING,
    Literal,
    Any
)
if TYPE_CHECKING:
    from src.application import Application

IPCTiming = Literal["before", "after"]
class PluginInfo:
    def __init__(self, name: str, author: str, version: str, description: str):
        self.name = name
        self.author = author
        self.version = version
        self.description = description

class Plugin:
    info: PluginInfo
    def __init__(self):
        self.enable = True


    def deinit(self):
        """
        插件被移除时触发
        """
        ...
    
    def on_app_before_initialize(self, app: "Application"):
        """
        应用程序初始化前触发
        
        :param app: 主程序实例
        """
        ...
    
    def on_app_after_initialized(self):
        """
        应用程序初始化后触发
        """
        ...
    
    def on_llm_response(self, chat_completion: ChatCompletionChunk | ChatCompletion):
        """
        大模型响应时触发
        
        :param chat_completion: 大模型回复的内容
        """
        ...
    
    def on_message_before_send(self, state: ChatState):
        """
        向智能体发送信息前触发
        
        :param state: 消息状态
        """
        ...
    
    def on_message_after_sended(self, state: ChatState):
        """
        向智能体发送信息后触发
        """
        ...

    def on_ready(self):
        """
        程序就绪时触发
        """
        ...
    
    def on_app_will_close(self):
        """
        向智能体发送信息前触发
        
        :param self: 插件实例
        """
        ...

    def emit(self, name: str, arguments: dict) -> Any:
        """
        用于插件与插件之间的通信
        :param name: 命令
        :type name: str
        :param arguments: 参数
        :type arguments: dict
        """
        ...
