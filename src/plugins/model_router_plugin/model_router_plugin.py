from src.components.ai_chat.chat_state import ChatState
from src.plugins.plugin import Plugin
from src.components.ai_chat import AIChat
from os import path
from src.components.logger import logger as log
import json
import os

from typing import (
    Literal,
    cast
)


logger = log.create(__name__)

TaskType = Literal["chat", "agent"]
class ModelRouterPlugin(Plugin):
    def __init__(self):
        super().__init__("model-router-plugin", desc="路由模型，分析用户输入选择Agent或者Chat模式")
        self.ai_chat = AIChat({
            "base_url": os.getenv("LLM_URL", "")
        })
        self.state = self.ai_chat.create_state(os.getenv("LLM_MODEL", ""))
        self.agent_prompt = ""
        self.chat_prompt = ""
    
    def get_prompt_content(self, type: Literal["chat", "agent", "model_router"]):
        root_path = path.abspath("prompts")
        prompt_path = path.join(root_path, f"{type}.md")
        if path.exists(prompt_path):
            with open(prompt_path, encoding="utf-8") as fs:
                return fs.read()
        raise FileNotFoundError(f"找不到提示词文件'{prompt_path}'")
    
    def init(self):
        try:
            self.state.fixed_sys_prompt = self.get_prompt_content("model_router")
            self.chat_prompt = self.get_prompt_content("chat")
            self.agent_prompt = self.get_prompt_content("agent")
        except FileNotFoundError as ex:
            logger.error(f"系统提示词加载失败: {ex}")
            super().state = False
            return
        self.state.set_thinking(False)
    
    def handle(self, user_input: str):
        self.state.user_input = user_input
        response_text, _ = self.ai_chat.complete(self.state)
        try:
            res: dict[str, str] = json.loads(response_text)
            type_value = res.get("type", "chat")
            type: TaskType = cast(TaskType, type_value)
            model = res.get("model")
            return type, model
        except Exception as ex:
            logger.error(f"出现异常: {ex}")
            return None, None
    
    def on_message_before_send(self, state: ChatState):
        type, model = self.handle(state.user_input)

        if type and model:
            state.model_name = model
            state.type = type

            if type == "agent":
                state.fixed_sys_prompt = self.agent_prompt
            elif type == "chat":
                state.fixed_sys_prompt = self.chat_prompt
