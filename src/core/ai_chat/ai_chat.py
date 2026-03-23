from openai.types.chat import ChatCompletionChunk
from typing import Callable
from openai import OpenAI
import sys
import os

from .types import EnvOptions, ServiceConfig
from .chat_session import ChatSession

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
    
    def create_session(self, model_name: str):
        session = ChatSession(model_name, [], [])
        return session
    
    def get_model_params(self):
        return {
            "model": "",
            "messages": [],
            "stream": True,
        }
    
    def _build_params(self, session: ChatSession):
        params = self.get_model_params()
        params["model"] = session.model_name
        params["messages"] = [
            {
                "role": "system",
                "content": session.system_prompt
            },
            *session.messages,
            {
                "role": "user",
                "content": session.user_prompt
            }
        ]
        if len(session.tools) > 0:
            params["tools"] = session.tools
        
        if len(session.extra_body) > 0:
            params["extra_body"] = session.extra_body
        return params

    def complete(self, session: ChatSession) -> tuple[str, str]:
        params = self._build_params(session)
        completion = self._client.chat.completions.create(**params)

        response_text = ""
        for chunk in completion:
            response_text += chunk.choices[0].delta.content
        
        return (response_text, chunk.choices[0].finish_reason)
    
    def start_response(self, session: ChatSession):
        params = self._build_params(session)
        completion = self._client.chat.completions.create(**params)

        # 处理流式回复
        for chunk in completion:
            if self.response_hook:
                self.response_hook(chunk, None)
        
        if self.response_hook:
            self.response_hook(None, chunk.choices[0].finish_reason)
    
    def bind_response_handler(self, hook: response_handler):
        self.response_hook = hook
