import os
from openai import OpenAI
from openai.types.chat import ChatCompletionChunk

from .types import EnvOptions, ServiceConfig
from .chat_session import ChatSession

class AIChat:
    def __init__(self, service_config: ServiceConfig, envs: EnvOptions = {}):
        self._client: OpenAI = OpenAI(
            api_key= os.getenv("DASHSCOPE_API_KEY"),
            base_url= service_config["base_url"]
        )
        self.model = service_config["model_name"]
        self.envs: EnvOptions = envs
        self.label_map = {
            "lang": "系统语言",
            "device": "用户设备",
            "network": "网络类型",
            "cpu": "CPU"
        }

    
    def _env_string(self):
        envs: list[str] = []

        for k,v in self.envs.items():
            label = self.label_map.get(k)
            if label:
                envs.append(f"- {label}: {v}")

        return "\n".join(envs)
    
    def create_session(self):
        session = ChatSession(self.model, [], [])
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
            self.on_reply(chunk, None)
        self.on_reply(None, chunk.choices[0].finish_reason)
    
    def on_reply(self, chunk: ChatCompletionChunk | None, finish_reason: str | None):
        """
        AI流式回复信息时触发
        """
        ...
