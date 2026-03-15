from openai.types.chat import ChatCompletionChunk
from typing import Callable
from openai import OpenAI
import sys
import os

from .types import EnvOptions, ServiceConfig
from .chat_session import ChatSession

response_handler = Callable[[ChatCompletionChunk | None, str | None], None]
class AIChat:
    def __init__(self, service_config: ServiceConfig, envs: EnvOptions = {}):
        api_key = service_config.get('api_key')
        api_key = api_key if api_key else os.getenv("DASHSCOPE_API_KEY")
        self._client: OpenAI = OpenAI(
            api_key= api_key,
            base_url= service_config["base_url"]
        )
        self.envs: EnvOptions = envs
        self.label_map = {
            "lang": "系统语言",
            "device": "用户设备",
            "network": "网络类型",
            "cpu": "CPU"
        }
        self.response_hook: response_handler | None = None
    
    def _get_user_env(self):
        ...

    def init(self, service_config: ServiceConfig):
        api_key = service_config.get('api_key')
        if api_key:
            self._client.api_key = api_key
        self._client.base_url = service_config['base_url']
    
    def _env_string(self):
        envs: list[str] = []

        for k,v in self.envs.items():
            label = self.label_map.get(k)
            if label:
                envs.append(f"- {label}: {v}")

        return "\n".join(envs)
    
    def create_session(self, model_name: str):
        session = ChatSession(model_name, [], [])
        if self.envs:
            sys_prompt_for_envs = f"""
# 用户系统环境
{
    self._env_string()
}
            """
            session.add_messages({
                "role": "system",
                "content": sys_prompt_for_envs
            })
        return session
    
    def get_model_params(self):
        return {
            "model": "",
            "messages": [],
            "stream": True,
        }

    
    def start_response(self, session: ChatSession):
        params = self.get_model_params()

        params["model"] = session.model_name
        params["messages"] = session.messages
        if len(session.tools) > 0:
            params["tools"] = session.tools
        
        if len(session.extra_body) > 0:
            params["extra_body"] = session.extra_body

        completion = self._client.chat.completions.create(**params)

        # 处理流式回复
        for chunk in completion:
            if self.response_hook:
                self.response_hook(chunk, None)
        
        if self.response_hook:
            self.response_hook(None, chunk.choices[0].finish_reason)
    
    def bind_response_handler(self, hook: response_handler):
        self.response_hook = hook
