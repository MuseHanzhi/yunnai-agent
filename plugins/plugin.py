from typing import Callable, TYPE_CHECKING, Iterator
from openai.types.chat import ChatCompletionChunk,ChatCompletionMessageParam
from PyQt6.QtWidgets import QWidget
from src.components.ai_chat.chat_session import ChatSession

if TYPE_CHECKING:
    from ..src.application import Application
    from ..src.ui import MainWindow

class Plugin:
    def __str__(self) -> str:
        return f"<plguin: {self.name}, author: {self.author}, ver: {self.version}, desc: {self.desc}, state: {self.state}>"

    def __init__(self, name: str, author: str = "", version: str = "1.0", desc: str = ""):
        self.name = name
        self.author = author
        self.version = version
        self.desc = desc
        self.state = True
    
    def init(self):
        ...

    def set_state(self, state: bool):
        self.state = state
    
    def on_app_before_initialize(self, app: "Application"):
        """
        应用程序初始化前触发
        
        :param self: 插件实例
        :param app: 主程序实例
        :type app: Application
        """
        ...
    
    def on_app_after_initialized(self):
        """
        应用程序初始化后触发
        """
        ...
    
    def on_ai_reply(self, chunk: ChatCompletionChunk):
        """
        智能体回复时触发
        
        :param content: 回复内容（流式）
        :type content: ChatCompletionChunk
        """
        ...
    
    def on_ai_reply_completed(self, finish_reason: str):
        ...
    
    def on_message_before_send(self, session: ChatSession, messages: Iterator[ChatCompletionMessageParam]):
        """
        向智能体发送信息前触发
        
        :param self: 插件实例
        :param message: 将要发送的信息
        """
        ...
    
    def on_message_after_sended(self):
        """
        向智能体发送信息后触发
        """
        ...

    def on_background_thread_start(self):
        ...
    
    def on_background_thread_end(self):
        ...
    
    def on_app_will_close(self, delay_request: Callable):
        """
        向智能体发送信息前触发
        
        :param self: 插件实例
        :param delay_request: 请求延时关闭，每次请求不能超过2秒 delay_request(2)
        :type delay_request: Callable
        """
        ...
    
    def on_window_hide(self, window: QWidget):
        ...
    
    def on_window_minimize(self, window: QWidget):
        ...
    
    def on_window_maximize(self, window: QWidget):
        ...
    
    def on_main_window_show(self, window: "MainWindow"):
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
