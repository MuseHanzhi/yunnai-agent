from openai.types.chat import ChatCompletionChunk
from plugins import Plugin
from src.tools import ToolManager
import json
from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QSize

if TYPE_CHECKING:
    from src.application import Application

class ToolsPlugin(Plugin):
    def __init__(self):
        super().__init__('tools_plugin')
        self.tools_manager = ToolManager()
        self.tool_info = {
            'id': '',
            'name': '',
            'arguments': ''
        }
        self.application: None | Application = None
        self.reply_message = ""
    
    def on_app_before_initialize(self, app: "Application"):
        self.application = app
        app.ai.set_tools(self.tools_manager.get_tools_schema())
    
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
        arguments = self.tool_info.get("arguments", "")

        self.tool_info = {
            'id': '',
            'name': '',
            'arguments': ''
        }

        dialog = QMessageBox()
        dialog.setFixedSize(QSize(400, 200))
        dialog.setWindowTitle(f"是否助手允许调用'{name}'工具？")
        dialog.setText(f"参数信息：{arguments}")

        dialog.setStandardButtons(
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )

        res = dialog.exec()
        result = QMessageBox.StandardButton(res)

        if result == QMessageBox.StandardButton.No:  # 拒绝调用处理
            self.application.send_message(
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
            })
        else:   # 允许调用工具
            call_result = self.tools_manager(name, json.loads(arguments))
            self.application.send_message(
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
                })
