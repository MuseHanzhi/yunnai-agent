from typing import (
    TYPE_CHECKING,
    Literal
)
from openai.types.chat import ChatCompletionChunk
from src.components.ai_chat.chat_state import ChatState
from asyncio import AbstractEventLoop

if TYPE_CHECKING:
    from src.application import Application

Hooks = Literal[
    "on_app_before_initialize",
    "on_app_after_initialized",
    "on_llm_response",
    "on_llm_response_completed",
    "on_app_will_close",
    "on_message_before_send",
    "on_message_after_sended",
    "on_ready"
]
class Plugin:
    def __str__(self) -> str:
        return f"<plguin: {self.name}, ver: {self.version}, desc: {self.desc}>"

    def __init__(self, name: str, version: str = "1.0", desc: str = ""):
        self.name = name
        self.version = version
        self.desc = desc
        self.hook_registry: list[Hooks] = []

    
    def init(self):
        """
        插件初始化时触发
        """
        ...

    def deinit(self):
        """
        插件被移除时触发
        """
        ...
    
    def on_app_before_initialize(self, app: "Application", event_loop: "AbstractEventLoop"):
        """
        应用程序初始化前触发
        
        :param app: 主程序实例
        :param event_loop: 异步事件循环（未运行）
        """
        ...
    
    def on_app_after_initialized(self, event_loop: "AbstractEventLoop"):
        """
        应用程序初始化后触发
        :param event_loop: 异步事件循环（未运行）
        """
        ...
    
    def on_llm_response(self, chunk: ChatCompletionChunk):
        """
        大模型响应时触发
        
        :param content: 回复内容（流式）
        :type content: ChatCompletionChunk
        """
        ...
    
    def on_llm_response_completed(self, finish_reason: str):
        """
        大模型响应完毕
        
        :param finish_reason: 完成原因：后续可能计划移除
        """
    
    def on_message_before_send(self, state: ChatState):
        """
        向智能体发送信息前触发
        
        :param state: 消息状态
        """
        ...
    
    def on_message_after_sended(self):
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

    def emit(self, name: str, arguments: dict):
        """
        用于插件与插件之间的通信
        :param name: 命令
        :type name: str
        :param arguments: 参数
        :type arguments: dict
        """
        ...
