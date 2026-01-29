from typing import Any, Callable

from openai.types.chat import ChatCompletionChunk
from application import Application
from .. import Plugin

class LogPlugin(Plugin):
    def __init__(self):
        super().__init__('logger_plugin')
    
    def app_before_initialize(self, app: Application):
        print("应用程序开始初始化")
    
    def app_after_initialize(self):
        print("应用程序初始化完毕")
    
    def app_will_close(self, delay_request: Callable[..., Any]):
        print("应用程序即将关闭")
    
    def app_closed(self):
        print("应用程序已关闭")
    
    def message_before_send(self, message: str):
        print(f"发送消息: {message}")
    
    def message_before_sended(self):
        print("消息已发送")
    
    def ai_reply(self, content: ChatCompletionChunk):
        return super().ai_reply(content)
