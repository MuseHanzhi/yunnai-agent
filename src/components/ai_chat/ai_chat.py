from openai.types.chat import ChatCompletionChunk, ChatCompletion, ChatCompletionMessageParam
from typing import Callable, Generator
from openai import OpenAI
from openai import AsyncOpenAI

from .types import ServiceConfig
from .chat_state import ChatState

response_handler = Callable[[ChatCompletionChunk], None]
class AIChat:
    def __init__(self, service_config: ServiceConfig):
        self._client: AsyncOpenAI = AsyncOpenAI(
            api_key= service_config["api_key"],
            base_url= service_config["base_url"]
        )
        self.model_name = service_config["model_name"]
    
    def reset_config(self, service_config: ServiceConfig):
        self._client.api_key = service_config["api_key"]
        self._client.base_url = service_config["base_url"]
        self.model_name = service_config["model_name"]
    
    def create_state(self, message: ChatCompletionMessageParam, is_stream: bool = True):
        state = ChatState(self.model_name, message=message, is_stream=is_stream)
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
        if state.message:
            params["messages"].append(state.message)
        
        if state.extra_body:
            params["extra_body"] = state.extra_body
        state.messages = params["messages"]
        return params

    async def non_stream_response(self, state: ChatState) -> ChatCompletion:
        if state.is_stream:
            raise ValueError("当前消息状态为流式响应，请使用'stream_response'方法")
        params = self._build_params(state)
        try:
            completion: ChatCompletion = await self._client.chat.completions.create(**params)
            return completion
        except:
            raise
    
    async def stream_response(self, state: ChatState):
        if not state.is_stream:
            raise ValueError("当前消息状态为非流式响应，请使用'non_stream_response'方法")
        params = self._build_params(state)
        try:
            async with self._client.chat.completions.create(**params) as completion:
                for chunk in completion:
                    yield chunk
        except:
            raise
