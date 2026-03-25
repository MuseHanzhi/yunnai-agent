from core.ai_chat.chat_state import ChatState
from src.plugins.plugin import Plugin
from typing import Literal, TYPE_CHECKING
from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam

if TYPE_CHECKING:
    from src.application import Application

class SessionPlugin(Plugin):
    def __init__(self):
        super().__init__("session-plugin", desc="管理会话")
        self.chat_records: list[ChatCompletionMessageParam] = []
        self.agent_records: list[ChatCompletionMessageParam] = []
        self.response_text: str = ""
        self.user_input: str = ""
        self.type: Literal["chat", "agent"] = "chat"
        self.app: "Application | None" = None
    
    def on_app_before_initialize(self, app: "Application"):
        self.app = app
    
    def on_message_before_send(self, state: ChatState):
        if self.type == "chat":
            state.messages = self.chat_records
        else:
            state.messages = self.agent_records
        self.user_input = state.user_input
        
        if self.type == "agent" and self.type != state.type:    # agent => chat时，清空任务对话记录
            self.agent_records = []    
        self.type = state.type
    
    def on_model_response(self, chunk: ChatCompletionChunk):
        if chunk.choices[0].delta.content:
            self.response_text += chunk.choices[0].delta.content
    
    def on_model_response_completed(self, finish_reason: str):
        if self.type == "chat":
            self.chat_records.append({
                "role": "user",
                "content": self.user_input
            })
            self.chat_records.append({
                "role": "assistant",
                "content": self.response_text
            })
        else:
            self.agent_records.append({
                "role": "user",
                "content": self.user_input
            })
            self.agent_records.append({
                "role": "assistant",
                "content": self.response_text
            })
        
        self.response_text = ""
        self.user_input = ""
