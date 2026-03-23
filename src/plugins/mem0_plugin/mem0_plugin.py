import os
from mem0 import Memory
import json

from openai.types.chat import ChatCompletionChunk

from src.core.ai_chat.chat_session import ChatSession
from src.plugins import Plugin
from src.core.ai_chat import AIChat

class Mem0Plugin(Plugin):
    def __init__(self):
        super().__init__("mem0-plugin", "1.0", "记忆库插件")
        self.memory = Memory()
        self.ai_chat = AIChat({
            "base_url": os.getenv("LLM_URL", "")
        })
        self.session = self.ai_chat.create_session(os.getenv("LLM_MODEL", ""))
        self.prompt = """
# 记忆
## 表示格式
内容:匹配度
## 用户记忆
{user_memory}
"""

    def init(self):
        self.session.append_system_prompt(self.read_prompt())
        self.session.set_thinking(False)

    def read_prompt(self):
        """
        读取prompt.md文件的内容
        Returns:
            str: 返回文件内容，如果文件不存在则返回空字符串
        """
        path = os.path  # 导入os.path模块
        prompt_path = path.join(path.abspath(path.dirname(__file__)), "prompt.md")
        if path.exists(prompt_path):
            with open(prompt_path, encoding="utf-8") as fs:
                return fs.read()
        return ""

    def search_memory(self, content: str, user_id: str):
        search_result = self.memory.search(content, user_id=user_id)
        memorys: list[dict] = search_result["results"]

        memory_items: list[str] = []
        for memory in memorys:
            memory_items.append(
                f"{memory.get("memory")}:{memory.get("score")}"
            )
        return "\n".join(memory_items)

    def handler(self, session: ChatSession, user_id: str):
        self.session.user_input = session.user_input
        text, _ = self.ai_chat.complete(self.session)
        result = json.loads(text)

        if result.get("mode") == "search":
            content = result.get("content")
            memory_text = self.search_memory(content, user_id)
            session.append_user_prompt(self.prompt.format(user_memory=memory_text))
            
        elif result.get("mode") == "add":
            content = result.get("content")
            self.memory.add(content)
        elif result.get("mode") == "delete":
            ...
        elif result.get("mode") == "update":
            ...
        

    def on_message_before_send(self, session: ChatSession):
        self.handler(session, "user")
