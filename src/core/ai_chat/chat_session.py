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
    
    def set_prompt(self, prompt_text):
        self.messages.append({
            "role": "system",
            "content": prompt_text
        })
    
    def add_tools(self, *tools: ChatCompletionToolUnionParam):
        for tool in tools:
            self.tools.append(tool)
    
    def add_messages(self, *messages: ChatCompletionMessageParam):
        for message in messages:
            self.messages.append(message)
    
    def set_extra_body(self, key: str, value: Any):
        self.extra_body[key] = value
    
    def clear(self):
        self.messages = []
        self.tools = []
        self.extra_body = {}
    
