from openai.types.chat import ChatCompletionChunk
from typing import Callable
from openai import OpenAI
import os

from .types import ServiceConfig
from .chat_state import ChatState

response_handler = Callable[[ChatCompletionChunk | None, str | None], None]
class AIChat:
    def __init__(self, service_config: ServiceConfig):
        api_key = service_config.get('api_key')
        api_key = api_key if api_key else os.getenv("DASHSCOPE_API_KEY")
        self._client: OpenAI = OpenAI(
            api_key= api_key,
            base_url= service_config["base_url"]
        )
        self.response_hook: response_handler | None = None

    def init(self, service_config: ServiceConfig):
        api_key = service_config.get('api_key')
        if api_key:
            self._client.api_key = api_key
        self._client.base_url = service_config['base_url']
    
    def create_state(self, model_name: str):
        state = ChatState(model_name, [], [])
        return state
    
    def get_model_params(self):
        return {
            "model": "",
            "messages": [],
            "stream": True,
        }
    
    def _build_params(self, state: ChatState):
        params = self.get_model_params()
        params["model"] = state.model_name
        params["messages"] = [
            *state.messages,
            {
                "role": "system",
                "content": state.system_prompt
            },
            {
                "role": "user",
                "content": state.user_input
            }
        ]
        if len(state.tools) > 0:
            params["tools"] = state.tools
        
        if len(state.extra_body) > 0:
            params["extra_body"] = state.extra_body
        return params

    def complete(self, state: ChatState) -> tuple[str, str]:
        params = self._build_params(state)
        completion = self._client.chat.completions.create(**params)

        response_text = ""
        for chunk in completion:
            response_text += chunk.choices[0].delta.content
        
        return (response_text, chunk.choices[0].finish_reason)
    
    def start_response(self, state: ChatState):
        params = self._build_params(state)
        completion = self._client.chat.completions.create(**params)

        # 处理流式回复
        for chunk in completion:
            if self.response_hook:
                self.response_hook(chunk, None)
        
        if self.response_hook:
            self.response_hook(None, chunk.choices[0].finish_reason)
    
    def bind_response_handler(self, hook: response_handler):
        self.response_hook = hook
