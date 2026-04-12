from openai.types.chat import ChatCompletionMessageParam
from typing import Any, Literal

class ChatState:
    def __init__(self, model_name: str, messages: list[ChatCompletionMessageParam] | None = None, is_stream: bool = True):
        self.messages = messages if messages else []
        self.model_name = model_name
        self.is_stream = is_stream
        self.extra_body: dict[str, Any] = {}
        self.canceled = False
        self.dynamic_sys_prompt = ""
        self.fixed_sys_prompt = ""
        self.user_input = ""
        self.msg_type: Literal["user", "system"] = "user"
        self.type: Literal["agent", "chat"] = "chat"
    
    def append_system_prompt(self, content: str):
        prompt = content if content.endswith("\n") else content + "\n"
        self.dynamic_sys_prompt += prompt
    
    def set_extra_body(self, key: str, value: Any):
        self.extra_body[key] = value
    
    def set_thinking(self, state: bool):
        self.extra_body["thinking"] = state
    
    def clear(self):
        self.messages = []
        self.tools = []
        self.extra_body = {}
    
