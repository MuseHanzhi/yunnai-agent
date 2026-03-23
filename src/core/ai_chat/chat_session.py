from openai.types.chat.chat_completion_tool_union_param import ChatCompletionToolUnionParam
from openai.types.chat import ChatCompletionMessageParam
from typing import Any

class ChatSession:
    def __init__(self, model_name: str, messages: list[ChatCompletionMessageParam] = [], tools: list[ChatCompletionToolUnionParam] = []):
        self.messages = messages
        self.tools = tools
        self.extra_body: dict[str, Any] = {}
        self.model_name = model_name
        self.canceled = False
        self.system_prompt = ""
        self.user_input = ""
        self.user_prompt = ""
    
    def add_tools(self, *tools: ChatCompletionToolUnionParam):
        for tool in tools:
            self.tools.append(tool)
    
    def append_system_prompt(self, content: str):
        prompt = content if content.endswith("\n") else content + "\n"
        self.system_prompt += prompt
    
    def append_user_prompt(self, content: str):
        prompt = content if content.endswith("\n") else content + "\n"
        self.user_prompt += prompt
    
    def set_extra_body(self, key: str, value: Any):
        self.extra_body[key] = value
    
    def set_thinking(self, state: bool):
        self.extra_body["thinking"] = state
    
    def clear(self):
        self.messages = []
        self.tools = []
        self.extra_body = {}
    
