from src.components.ai_chat.chat_state import ChatState
from src.plugins.plugin import Plugin
from typing import Literal, TYPE_CHECKING
from openai.types.chat import ChatCompletion, ChatCompletionChunk, ChatCompletionMessageParam

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
        self.hook_registry = [
            "on_app_before_initialize",
            "on_message_before_send",
            "on_llm_response"
        ]
    
    def on_app_before_initialize(self, app: "Application", event_loop):
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
    
    def on_llm_response(self, chat_completion: "ChatCompletionChunk | ChatCompletion"):
        if chat_completion.choices:
            return
        if isinstance(chat_completion, ChatCompletionChunk):
            content = chat_completion.choices[0].delta.content
            self.response_text += content if content else ""
        elif isinstance(chat_completion, ChatCompletion):
            content = chat_completion.choices[0].message.content
            self.response_text += content if content else ""

        if chat_completion.choices[0].finish_reason:
            self.on_llm_response_completed()
    
    def on_llm_response_completed(self):
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
