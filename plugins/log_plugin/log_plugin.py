from typing import Any, Callable, TYPE_CHECKING, Iterator
from PyQt6.QtWidgets import QWidget
from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam
from src.components.ai_chat.chat_session import ChatSession
from plugins import Plugin
import json

if TYPE_CHECKING:
    from ...src.application import Application

class LogPlugin(Plugin):
    def __init__(self, name: str):
        super().__init__(name, desc="TTS，在程序的某个关键时刻输出日志")
        self.replying = False
    
    def on_app_before_initialize(self, app: "Application"):
        print("应用程序开始初始化")
    
    def on_app_after_initialized(self):
        print("应用程序初始化完毕")
    
    def on_app_will_close(self, delay_request: Callable[..., Any]):
        print("应用程序即将关闭")
    
    def on_app_closed(self):
        print("应用程序已关闭")
    
    def on_message_before_send(self, session: ChatSession, messages):
        print("消息开始发送")
    
    def on_message_after_sended(self):
        print("消息已发送")

    def on_background_thread_start(self):
        ...
    
    def on_ai_reply(self, chunk: ChatCompletionChunk):
        if not self.replying:
            print("智能体开始响应")
    
    def on_ai_reply_completed(self, finish_reason: str):
        print("智能体响应完毕")

    def on_window_hide(self, window: QWidget):
        print("窗体隐藏")
    
    def on_window_maximize(self, window: QWidget):
        print("窗体最大化")
    
    def on_window_minimize(self, window: QWidget):
        print("窗体最小化")
