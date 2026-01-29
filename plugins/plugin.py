from typing import Callable, TYPE_CHECKING
from openai.types.chat import ChatCompletionChunk

if TYPE_CHECKING:
    from ..src.application import Application

class Plugin:
    def __str__(self) -> str:
        return f"<plguin: {self.name}, author: {self.author}, ver: {self.version}>"

    def __init__(self, name: str, author: str = "", version: str = "1.0"):
        self.name = name
        self.author = author
        self.version = version
    
    def app_before_initialize(self, app: "Application"):
        """
        应用程序初始化前触发
        
        :param self: 插件实例
        :param app: 主程序实例
        :type app: Application
        """
        ...
    
    def app_after_initialize(self):
        """
        应用程序初始化后触发
        """
        ...
    
    def ai_reply(self, content: ChatCompletionChunk):
        """
        智能体回复时触发
        
        :param content: 回复内容（流式）
        :type content: ChatCompletionChunk
        """
        ...
    
    def message_before_send(self, message: str):
        """
        向智能体发送信息前触发
        
        :param self: 插件实例
        :param message: 将要发送的信息
        """
        ...
    
    def message_before_sended(self):
        """
        向智能体发送信息后触发
        """
        ...
    
    def app_will_close(self, delay_request: Callable):
        """
        向智能体发送信息前触发
        
        :param self: 插件实例
        :param delay_request: 请求延时关闭，每次请求不能超过2秒 delay_request(2)
        :type delay_request: Callable
        """
        ...
    
    def app_closed(self):
        ...
