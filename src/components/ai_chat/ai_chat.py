from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionChunk
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
    
    def send(self, *messages: ChatCompletionMessageParam):
        for message in messages:
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


        # 处理流式回复
        for chunk in completion:
            self.on_reply(chunk, None)
        self.on_reply(None, chunk.choices[0].finish_reason)
    
    def on_reply(self, chunk: ChatCompletionChunk | None, finish_reason: str | None):
        """
        AI流式回复信息时触发
        """
        ...
