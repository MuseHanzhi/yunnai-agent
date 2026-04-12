from openai.types.chat import ChatCompletionChunk
from typing import Callable
from openai import OpenAI

from .types import ServiceConfig
from .chat_state import ChatState

response_handler = Callable[[ChatCompletionChunk], None]
class AIChat:
    def __init__(self, service_config: ServiceConfig):
        self._client: OpenAI = OpenAI(
            api_key= service_config["api_key"],
            base_url= service_config["base_url"]
        )
        self.model_name = service_config["model_name"]
        
    
    def create_state(self, is_stream: bool = True):
        state = ChatState(self.model_name, is_stream=is_stream)
        return state
    
    def _build_params(self, state: ChatState):
        params = {
            "model": state.model_name,
            "stream": state.is_stream,
            "messages": [
                {
                    "role": "system",
                    "content": state.fixed_sys_prompt   # 固定prompt，
                },
                *state.messages
            ]
        }

        if state.dynamic_sys_prompt:
            # 动态prompt，一些附加信息，比如MCP列表、技能列表、系统信息、时间信息等
            params["messages"].append({
                "role": "system",
                "content": state.dynamic_sys_prompt
            })
        # 要求大模型响应的信息
        params["messages"].append({
            "role": state.msg_type,
            "content": state.user_input
        })
        
        if state.extra_body:
            params["extra_body"] = state.extra_body
        return params

    def non_stream_response(self, state: ChatState):
        if state.is_stream:
            raise ValueError("当前消息状态为流式响应，请使用'stream_response'方法")
        params = self._build_params(state)
        try:
            with self._client.chat.completions.create(**params) as completion:
                return completion
        except:
            raise
    
    def stream_response(self, state: ChatState):
        if not state.is_stream:
            raise ValueError("当前消息状态为非流式响应，请使用'non_stream_response'方法")
        params = self._build_params(state)
        try:
            with self._client.chat.completions.create(**params) as completion:
                for chunk in completion:
                    yield chunk
        except:
            raise
