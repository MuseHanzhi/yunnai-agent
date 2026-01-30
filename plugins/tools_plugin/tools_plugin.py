from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam
# from PyQt6.QtWidgets import QMessageBox
from src.tools import ToolManager
from typing import TYPE_CHECKING
# from PyQt6.QtCore import QSize
from plugins import Plugin
import logging
import asyncio
import typing
import json

if TYPE_CHECKING:
    from src.application import Application

class ToolsPlugin(Plugin):
    def __init__(self, name: str, inner_tool: dict[str, typing.Callable] = {}, inner_flag: str = "application"):
        super().__init__(name)
        self.logger = logging.Logger(__name__)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(console_handler)

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
        
    
    def on_app_before_initialize(self, app: "Application"):
        self.application = app
        app.ai.set_tools(self.tools_manager.get_tools_schema())
        self.event_loop = asyncio.get_event_loop()
    
    def on_ai_reply(self, chunk: ChatCompletionChunk):
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
    
    def on_ai_reply_completed(self, finish_reason):
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

        # dialog = QMessageBox()
        # dialog.setFixedSize(QSize(400, 200))
        # dialog.setWindowTitle(f"提示")
        # dialog.setText(f"是否助手允许调用'{name}'工具？\n参数信息：{arguments}")

        # dialog.setStandardButtons(
        #     QMessageBox.StandardButton.Yes |
        #     QMessageBox.StandardButton.No
        # )

        # res = dialog.exec()
        # result = QMessageBox.StandardButton(res)
        messages = self.allow_call(id, name, arguments)
        if self.event_loop:
            self.event_loop.create_task(self.send_message(*messages))
        # if result == QMessageBox.StandardButton.No:  # 拒绝调用处理
        #     self.reject_call(id, name, arguments)
        # else:   # 允许调用工具
        #     self.allow_call(id, name, arguments)
    
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
        self.logger.info(f"调用工具: '{name}'，参数: {arguments}，id: {id}")
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
