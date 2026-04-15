from openai.types.chat import ChatCompletionMessageParam
from typing import Any, Literal

class ChatState:
    def __init__(self, model_name: str, message: ChatCompletionMessageParam, messages: list[ChatCompletionMessageParam] | None = None, is_stream: bool = True):
        self.messages = messages if messages else []
        self.model_name = model_name
        self.is_stream = is_stream
        self.extra_body: dict[str, Any] = {}
        self.canceled = False
        self.dynamic_sys_prompt = ""
        self.fixed_sys_prompt = ""
        self.msg_type: Literal["user", "system"] = "user"
        self.type: Literal["agent", "chat"] = "chat"
        self.mcp_list: list[dict] = []
        self.message: ChatCompletionMessageParam = message
    
    def set_mcp_list(self, mcp_list: list[dict]):
        self.mcp_list = mcp_list
    
    def to_dict(self) -> dict:
        return {
            "model": self.model_name,
            "messages": self.messages,
            "stream": self.is_stream,
            "extra_body": self.extra_body,
            "canceled": self.canceled,
            "dynamic_sys_prompt": self.dynamic_sys_prompt,
            "fixed_sys_prompt": self.fixed_sys_prompt,
            "msg_type": self.msg_type,
            "type": self.type,
            "message": self.message
        }
    
    def change_from_dict(self, data: dict):
        self.messages = data["messages"]
        self.model_name = data["model"]
        self.is_stream = data["stream"]
        self.extra_body = data["extra_body"]
        self.canceled = data["canceled"]
        self.dynamic_sys_prompt = data["dynamic_sys_prompt"]
        self.fixed_sys_prompt = data["fixed_sys_prompt"]
        self.msg_type = data["msg_type"]
        self.type = data["type"]
        self.message = data["message"]


    def cancel(self):
        self.canceled = True

    def append_system_prompt(self, content: str):
        prompt = content if content.endswith("\n") else content + "\n"
        self.dynamic_sys_prompt += prompt
    
    
    def set_extra_body(self, key: str, value: Any):
        self.extra_body[key] = value
    
    def clear(self):
        self.messages = []
        self.tools = []
        self.extra_body = {}
    
