from typing import Any, Callable, TYPE_CHECKING
from PyQt6.QtWidgets import QWidget
from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam
from plugins import Plugin
import json

if TYPE_CHECKING:
    from ...src.application import Application

class LogPlugin(Plugin):
    def __init__(self, name: str):
        super().__init__(name)
    
    def on_app_before_initialize(self, app: "Application"):
        print("应用程序开始初始化")
    
    def on_app_after_initialized(self):
        print("应用程序初始化完毕")
    
    def on_app_will_close(self, delay_request: Callable[..., Any]):
        print("应用程序即将关闭")
    
    def on_app_closed(self):
        print("应用程序已关闭")
    
    def on_message_before_send(self, *messages: ChatCompletionMessageParam):
        print(f"发送消息: {messages}")
    
    def on_message_before_sended(self):
        print("消息已发送")
    
    def on_ai_reply(self, content: ChatCompletionChunk):
        return super().on_ai_reply(content)

    def on_background_thread_start(self):
        ...

    def on_window_hide(self, window: QWidget):
        print("窗体隐藏")
    
    def on_window_maximize(self, window: QWidget):
        print("窗体最大化")
    
    def on_window_minimize(self, window: QWidget):
        print("窗体最小化")
