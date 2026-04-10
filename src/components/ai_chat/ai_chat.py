from openai.types.chat import ChatCompletionChunk
from typing import Callable
from openai import OpenAI
import os

from .types import ServiceConfig
from .chat_state import ChatState

response_handler = Callable[[ChatCompletionChunk | None, str | None], None]
class AIChat:
    def __init__(self, service_config: ServiceConfig):
        self._client: OpenAI = OpenAI(
            api_key= service_config["api_key"],
            base_url= service_config["base_url"]
        )
        self.response_hook: response_handler | None = None
        self.model_name = service_config["model_name"]
    
    def create_state(self):
        state = ChatState(self.model_name)
        return state
    
    def get_model_params(self):
        return {
            "model": "",
            "messages": [],
            "stream": True,
        }
    
    def _build_params(self, state: ChatState):
        params = self.get_model_params()
        system_prompt = state.fixed_sys_prompt.replace("{dynamic_prompt}", state.dynamic_sys_prompt)
        params["model"] = state.model_name
        params["messages"] = [
            {
                "role": "system",
                "content": system_prompt
            },
            *state.messages,
            {
                "role": state.msg_type,
                "content": state.user_input
            }
        ]
        
        if len(state.extra_body) > 0:
            params["extra_body"] = state.extra_body
        return params

    def complete(self, state: ChatState) -> tuple[str, str]:
        params = self._build_params(state)
        with self._client.chat.completions.create(**params) as completion:
            response_text = ""
            for chunk in completion:
                response_text += chunk.choices[0].delta.content
            return (response_text, chunk.choices[0].finish_reason)
    
    def start_response(self, state: ChatState):
        params = self._build_params(state)
        with self._client.chat.completions.create(**params) as completion:
            # 处理流式回复
            for chunk in completion:
                if self.response_hook:
                    self.response_hook(chunk, None)
            
            if self.response_hook:
                self.response_hook(None, chunk.choices[0].finish_reason)
    
    def bind_response_handler(self, hook: response_handler):
        self.response_hook = hook
