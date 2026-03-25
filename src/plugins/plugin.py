from typing import TYPE_CHECKING, Iterator
from openai.types.chat import ChatCompletionChunk,ChatCompletionMessageParam
from src.core.ai_chat.chat_state import ChatState

if TYPE_CHECKING:
    from src.application import Application

class Plugin:
    def __str__(self) -> str:
        return f"<plguin: {self.name}, ver: {self.version}, desc: {self.desc}, state: {self.state}>"

    def __init__(self, name: str, version: str = "1.0", desc: str = ""):
        self.name = name
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
        
        :param app: 主程序实例
        """
        ...
    
    def on_app_after_initialized(self):
        """
        应用程序初始化后触发
        """
        ...
    
    def on_model_response(self, chunk: ChatCompletionChunk):
        """
        大模型响应时触发
        
        :param content: 回复内容（流式）
        :type content: ChatCompletionChunk
        """
        ...
    
    def on_model_response_completed(self, finish_reason: str):
        """
        大模型响应完毕
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
