from typing import Literal, TYPE_CHECKING
import asyncio

from openai.types.chat import ChatCompletion, ChatCompletionChunk, ChatCompletionMessageParam

from src.components.ai_chat.chat_state import ChatState
from src.plugins.plugin import Plugin
from src.plugins.hook_registry import registry


if TYPE_CHECKING:
    from src.application import Application

class SessionPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.chat_records: list[ChatCompletionMessageParam] = []
        self.agent_records: list[ChatCompletionMessageParam] = []
        self.response_text: str = ""
        self.end_message: ChatCompletionMessageParam | None = None
        self.type: Literal["chat", "agent"] = "chat"
        self.app: "Application | None" = None
        self.future: asyncio.Future | None = asyncio.Future()
    

    @registry.on_app_before_initialize()
    def on_app_before_initialize(self, app: "Application"):
        self.app = app
    
    @registry.on_message_before_send()
    def on_message_before_send(self, state: ChatState):
        if self.type == "chat":
            state.messages = self.chat_records
            # if len(self.chat_records) <= 20:
                
            # else:
            #     state.messages = self.chat_records[len(self.chat_records) - 20:]
        else:
            state.messages = self.agent_records
        
        if self.type == "agent" and self.type != state.type:    # agent => chat时，清空任务对话记录
            self.agent_records = []
        self.type = state.type
    
    @registry.on_message_after_sended()
    def on_message_after_sended(self, state: ChatState):
        if self.type == "chat":
            self.chat_records.append(state.message)
        elif self.type == "agent":
            self.agent_records.append(state.message)
    
    @registry.on_llm_response()
    def on_llm_response(self, chat_completion: "ChatCompletionChunk | ChatCompletion"):
        if not chat_completion.choices:
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
                "role": "assistant",
                "content": self.response_text
            })
        else:
            self.agent_records.append({
                "role": "assistant",
                "content": self.response_text
            })
        
        self.response_text = ""
    
    def emit(self, name: str, arguments: dict):
        if name == "get_chat_records":
            return self.chat_records
        if name == "get_agent_records":
            return self.agent_records
        if name == "add_records":
            type = arguments.get("type")
            if not type:
                return
            records = arguments.get("records", [])
            for item in records:
                if type == "agent":
                    self.agent_records.append(item)
                else:
                    self.chat_records.append(item)

