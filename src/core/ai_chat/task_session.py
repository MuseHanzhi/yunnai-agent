from .types import (
    ToolMessage,
    ChatMessage,
    Tool
)
from typing import Literal
import json

class TaskSession:
    def __init__(self, task_id: str, user_question: str, mcp_name: str, top_prompt:str ="", prompt_template: str = "", task_type: str = "normal"):
        self.chat_messages: list[ChatMessage] = []          # 会话历史消息
        self.id = task_id                                   # 任务ID
        self.tool_result: dict[str, ToolMessage] = {}       # 工具执行结果
        self.tools: list[Tool] = []                         # 工具列表
        self.user_question: str = user_question             # 用户问题
        self.mcp_name: str = mcp_name                       # mcp名称
        self.top_prompt = top_prompt                        # 顶级提示词
        self.prompt_template = prompt_template
        self.task_type = task_type

    def build(self) -> list[ChatMessage]:
        system_prompt = self.prompt_template.format(
            mcp_name = self.mcp_name,
            user_demand = self.user_question,
            tools=self.build_tool_schema(),
            task_type = self.task_type
            )

        return [
            {
                "role": "system",
                "content": system_prompt
            },
            *self.chat_messages
        ]
    
    def add_tool_result(self, call_id: str, tool_name: str, result: str, desc: str):
        """
        增加对话消息，工具执行结果
        Args:
          `call_id`: 工具调用id
          `tool_name`: 工具名称
          `result`: 工具执行结果
          `desc`: 执行描述
        """
        tool_content_template = '{"name": {0}, "result": {1}, "desc": {2}}'
        self.chat_messages.append({
            "role": "tool",
            "content": f"执行结果: {tool_content_template.format(tool_name, result, desc)}"
        })
        self.tool_result[call_id] = {
            "role": "tool",
            "id": call_id,
            "name": tool_name,
            "result": result,
            "desc": desc
        }

    def add_message(self, role: Literal["user", "assistant"], content: str):
        self.chat_messages.append({
            "role": role,
            "content": content
        })
    
    def build_tool_schema(self):
        result: list[str] = []
        for tool in self.tools:
            result.append(json.dumps(tool))
        return "\n".join(result)
