from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolMessageParam
from openai.types.chat.chat_completion_tool_union_param import ChatCompletionToolUnionParam
import os
import json

class AIChat:

    def __init__(self, system_prompt=""):
        self.__client = OpenAI(
            api_key= os.getenv('DASHSCOPE_API_KEY'),
            base_url= 'https://dashscope.aliyuncs.com/compatible-mode/v1'
        )

        self.__tools: list[ChatCompletionToolUnionParam] = []
        self.__messages: list[ChatCompletionMessageParam] = []
        if system_prompt:
            self.__messages.append({
                'role': 'system',
                'content': system_prompt
            })

    
    def add_tool(self, tool: ChatCompletionToolUnionParam):
        self.__tools.append(tool)
    
    def set_tools(self, tools: list[ChatCompletionToolUnionParam]):
        self.__tools = tools
    
    def send(self, message: ChatCompletionMessageParam):
        self.__messages.append(message)
        self.__create_chat()
    
    def __create_chat(self):
        params = {
            "model": "qwen-plus",
            "messages": self.__messages,
            "stream": True,
            "extra_body": {
                "enable_search": True
            }
        }

        if len(self.__tools) > 0:
            params['tools'] = self.__tools

        completion = self.__client.chat.completions.create(**params)

        reply_message = ""

        tool_info = {
            "id": "",
            "name": "",
            "arguments": ""
        }

        # 处理流式回复
        for chunk in completion:
            data = chunk.choices[0].model_dump()
            delta = data['delta']
            tool = delta.get("tool_calls", None)
            if(tool == None):   # 普通信息回复
                content = delta.get('content', None)
                if content:
                    reply_message += content
                    self.on_reply(content)
                    
            elif not tool is None:  # 收集工具调用信息
                id = tool[0].get("id", None)
                function_info = tool[0].get("function", {})
                function_name = function_info.get("name", None)
                arguments = function_info.get("arguments", None)

                tool_info["id"] += id if id else ''
                tool_info["name"] += function_name if function_name else ''
                tool_info["arguments"] += arguments if arguments else ''

        # 回复结束
        finish_reason = chunk.choices[0].finish_reason
        if finish_reason == "tool_calls":
            argument_dict = {
                **tool_info,
                "arguments": json.loads(tool_info["arguments"])
            }

            self.__messages.append({
                'role': 'assistant',
                'content': reply_message,
                'tool_calls': [
                    {
                        'id': tool_info['id'],
                        'type': 'function',
                        'function': {
                            'name': tool_info['name'],
                            'arguments': tool_info['arguments']
                        }
                    }
                ]
            })

            self.on_call_tool(**argument_dict)
            
        elif finish_reason == "stop":
            self.finish_stop({
                'role': 'assistant',
                'content': reply_message
            })
    
    def finish_stop(self, assistant_msg: ChatCompletionMessageParam):
        self.on_reply('')
        self.__messages.append(assistant_msg)
    
    def on_reply(self, message: str):
        """
        AI流式回复普通信息时触发
        """
        ...
    
    def on_call_tool(self, id: str, name: str, arguments: dict):
        """
        AI调用工具时触发
        """
        ...
