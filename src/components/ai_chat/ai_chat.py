from openai import OpenAI
from openai.types.chat import ChatCompletionChunk
import os
from .chat_session import ChatSession

class AIChat:

    def __init__(self, base_url: str, model_name: str):
        self.__client = OpenAI(
            api_key= os.getenv('DASHSCOPE_API_KEY'),
            base_url= base_url
        )

        self.model = model_name
    
    def create_session(self):
        session = ChatSession(self)
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

        completion = self.__client.chat.completions.create(**params)

        # 处理流式回复
        for chunk in completion:
            self.on_reply(chunk, None)
        self.on_reply(None, chunk.choices[0].finish_reason)
    
    def on_reply(self, chunk: ChatCompletionChunk | None, finish_reason: str | None):
        """
        AI流式回复信息时触发
        """
        ...
