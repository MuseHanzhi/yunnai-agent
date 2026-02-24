from openai import OpenAI
from openai.types.chat import ChatCompletionChunk

from .types import EnvOptions, ServiceConfig
from .chat_session import ChatSession

class AIChat:
    def __init__(self, model_name: str):
        self._client: OpenAI = OpenAI(api_key="")
        self.model = model_name
        self.envs: EnvOptions = {}
        self.label_map = {
            "lang": "系统语言",
            "device": "用户设备",
            "network": "网络类型",
            "cpu": "CPU"
        }
    
    def init(self, service_config: ServiceConfig, envs: EnvOptions = {}):
        api_key = service_config.get("api_key")
        if not api_key:
            raise Exception("服务配置项'api_key'是必须的")
        self._client.api_key = api_key

        base_url = service_config.get("base_url")
        if base_url:
            self._client.base_url = base_url

        self.envs = envs
    
    def _env_string(self):
        envs: list[str] = []

        for k,v in self.envs.items():
            label = self.label_map.get(k)
            if label:
                envs.append(f"- {label}: {v}")

        return "\n".join(envs)
    
    def create_session(self):
        session = ChatSession([], [])
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
            "model": self.model,
            "messages": [],
            "stream": True,
        }

    
    def start_response(self, session: ChatSession):
        params = self.get_model_params()

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
