from application import Application
from src.plugins.plugin import Plugin
from src.core.ai_chat.ai_chat import (
    AIChat,
    ChatSession
)
from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam
import typing
import asyncio
import json
import os

from .types.change_model import ChangeModelOption

if typing.TYPE_CHECKING:
    from src.application import Application

class ModelRouterPlugin(Plugin):
    def __init__(self):
        super().__init__("model-router-plugin", desc="根据用户输入，切换模型")
        
        llm_api_url = os.getenv("LLM_URL")
        llm_api_key = os.getenv("DASHSCOPE_API_KEY")
        if llm_api_key is None or llm_api_url is None:
            raise Exception("未设定环境变量 'LLM_URL' 或 'DASHSCOPE_API_KEY'")
        
        self.ai_chat: AIChat = AIChat({
            "api_key": llm_api_key,
            "base_url": llm_api_url
        })
        self.app: "Application |  None" = None
        self.result: ChangeModelOption | None = None
        self.target_model: str | None = None
        self.chat_history: list[ChatCompletionMessageParam] = []
        self.response_text: str = ""
    
    def on_app_before_initialize(self, app: Application):
        self.app = app
        self.ai_chat.bind_response_handler(self.on_router_model_response)
    
    def on_router_model_response(self, chunk: ChatCompletionChunk | None, finish_reason: str | None):
        if chunk and finish_reason is None and chunk.choices[0].delta.content:
            self.response_text += chunk.choices[0].delta.content
        elif finish_reason:
            self.result = self.try_parse_json(self.response_text)
            if self.result is None and self.app:
                asyncio.get_event_loop()\
                    .create_task(
                        self.app.ipc.emit(
                            'main_window',
                            "ai-response",
                            message = self.response_text,
                            model_name = "model_router"
                            )
                        )
            else:
                self.result = {
                    "model": "no-result",
                    "prompt_name": "model_router"
                }
            

    @staticmethod
    def try_parse_json(json_string: str) -> typing.Optional[ChangeModelOption]:
        try:
            return json.loads(json_string)
        except:
            return None
        
    @staticmethod
    def read_prompt_text(name: typing.Literal["chat", "agent", "model_router"]):
        base_path = os.path.abspath("prompts")
        prompt_file = os.path.join(base_path, f"{name}.md")
        with open(prompt_file, "r", encoding="utf-8") as f:
            return f.read()
    
    async def start(self, *user_message: ChatCompletionMessageParam):
        session = self.ai_chat.create_session("deepseek-chat")

        system_prompt = self.read_prompt_text("model_router")
        session.set_system_prompt(system_prompt)
        session.add_messages(*user_message)
        self.ai_chat.start_response(session)
    
    def on_message_before_send(self, session: ChatSession):
        if session.model_name == "model_router":
            return
        
        event_loop = asyncio.get_event_loop()
        event_loop.create_task(self.start(*session.messages))
        self.result = None

        while not self.result:  # 阻塞，直到有结果为止
            event_loop.run_until_complete(asyncio.sleep(0.5))
        if self.result['model'] != "no-result":
            session.model_name = self.result["model"]
            session.messages.pop()  # 弹出最后一个用户消息
            session.add_messages(*self.chat_history)    # 这里面有刚刚弹出的用户消息

            # 设置相应的系统提示词
            system_prompt = self.read_prompt_text(self.result["prompt_name"])
            session.set_system_prompt(system_prompt)
            