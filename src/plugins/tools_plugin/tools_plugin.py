from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam
from typing import TYPE_CHECKING, Callable
import asyncio
import json

from src.components.logger import logger as log
from src.core.ai_chat.chat_session import ChatSession
from .tool_manager import ToolManager
from plugins import Plugin

if TYPE_CHECKING:
    from src.application import Application

logger = log.create(__name__)

class ToolsPlugin(Plugin):
    def __init__(self, name: str, inner_tool: dict[str, Callable] = {}, inner_flag: str = "application"):
        super().__init__(name, desc="TTS，给予智能体调用工具的能力")

        self.inner_flag = inner_flag
        self.tools_manager = ToolManager()
        self.tool_info = {
            'id': '',
            'name': '',
            'arguments': ''
        }
        self.application: None | Application = None
        self.reply_message = ""
        self.inner_tools = inner_tool
        self.event_loop: asyncio.AbstractEventLoop | None = None
        
    def on_message_before_send(self, session: ChatSession, messages):
        session.add_tools(*self.tools_manager.get_tools_schema())
    
    def on_app_before_initialize(self, app: "Application"):
        self.application = app
    
    def on_ready(self):
        self.event_loop = asyncio.get_event_loop()
    
    def on_model_response(self, chunk: ChatCompletionChunk):
        data = chunk.choices[0].model_dump()
        delta = data['delta']
        tool = delta.get("tool_calls", None)
        if(tool == None):   # 普通信息回复
            content = delta.get('content', None)
            if content:
                self.reply_message += content
            return

        if not tool is None:  # 收集工具调用信息
            id = tool[0].get("id", None)
            function_info = tool[0].get("function", {})
            function_name = function_info.get("name", None)
            arguments = function_info.get("arguments", None)

            self.tool_info["id"] += id if id else ''
            self.tool_info["name"] += function_name if function_name else ''
            self.tool_info["arguments"] += arguments if arguments else ''
    
    def on_model_response_completed(self, finish_reason):
        if not self.application or finish_reason == "stop":
            return
        
        id = self.tool_info.get("id", "")
        name = self.tool_info.get("name", "")
        arguments = self.tool_info.get("arguments", "{}")

        self.tool_info = {
            'id': '',
            'name': '',
            'arguments': ''
        }

        messages = self.allow_call(id, name, arguments)
        if self.event_loop:
            self.event_loop.create_task(self.send_message(*messages))
    
    async def send_message(self, *messages: ChatCompletionMessageParam):
        if not self.application:
            return
        self.application.send_message(*messages)
        await asyncio.sleep(0.01)

    
    def reject_call(self, id, name, arguments) -> list[ChatCompletionMessageParam]:
        return [
            {
                'role': 'assistant',
                'content': self.reply_message,
                'tool_calls': [
                    {
                        'id': id,
                        'type': 'function',
                        'function': {
                            'name': name,
                            'arguments': arguments
                        }
                    }
                ]
            },
            {
                'role': 'tool',
                'tool_call_id': id,
                'content': '用户拒绝调用'
            }
        ]
    
    def allow_call(self, id: str, name: str, arguments: str) -> list[ChatCompletionMessageParam]:
        logger.info(f"调用工具: '{name}'，参数: {arguments}，id: {id}")
        names = name.split('.')
        call_result = None
        if names[0] != self.inner_flag:
            call_result = self.tools_manager(name, json.loads(arguments))
        else:
            call_result = self.inner_tools[names[1]](**json.loads(arguments))
        return [
            {
                'role': 'assistant',
                'content': self.reply_message,
                'tool_calls': [
                    {
                        'id': id,
                        'type': 'function',
                        'function': {
                            'name': name,
                            'arguments': arguments
                        }
                    }
                ]
            },
            {
                'role': 'tool',
                'tool_call_id': id,
                'content': json.dumps(call_result)
            }
        ]
