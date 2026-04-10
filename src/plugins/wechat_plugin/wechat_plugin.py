from openai.types.chat import ChatCompletionChunk

from src.common import public_tools
from src.components.ai_chat.chat_state import ChatState
from src.plugins import Plugin
from src.components.logger.logger import create
from .wechat_bot.wechat_client import WeChatClient
from wxautox4 import Chat
from wxautox4.msgs import (
    BaseMessage,
    TextMessage,
    VoiceMessage,
    EmotionMessage,
    ImageMessage,
    HumanMessage
)
import typing
import asyncio
import random
import json
import re
from datetime import datetime

if typing.TYPE_CHECKING:
    from src.application import Application

logger = create(__name__)

class TaskUnit(typing.TypedDict):
    name: str
    message: BaseMessage
    future: asyncio.Future

class WeChatPlugin(Plugin):
    def __init__(self):
        super().__init__("wechat_plugin")
        self.client = WeChatClient()
        self.app: "Application | None" = None
        self.llm_text = ""
        self.future: asyncio.Future | None = None
        self.send_messages: list[str] = []
        self.handling = False
        self.tasks: dict[str, TaskUnit] = {}
        self.results: dict[str, asyncio.Future] = {}
    
    def on_wechat_message(self, message, chat: Chat):
        logger.info(f"接收到{chat.who}的消息: {message}")
        text: str
        if isinstance(message, VoiceMessage):
            text = message.to_text()
        elif isinstance(message, TextMessage):
            text = message.content
        elif isinstance(message, EmotionMessage):
            text = f"[发送了一张表情包: {message.content}]"
        elif isinstance(message, ImageMessage):
            message.download()
            return
        else:
            return
        if not self.handling:
            self.handling = True
            self.send_messages.append(text)
            asyncio.run(self.send_message(message, chat))
        else:
            self.send_messages.append(text)

        # event_loop.run_forever()
    
    async def search(self, search_info: dict, message: BaseMessage, chat: Chat):
        if not isinstance(message, HumanMessage) or self.app is None:
            return
        id: str = search_info["id"]
        future = asyncio.Future[str]()
        self.tasks[id] = {
            "name": "web_search",
            "future": future,
            "message": message
        }

        search_result = await future

        self.tasks.pop(id)

        event_loop = asyncio.get_running_loop()
        event_loop.create_task(self.app.sync_send_message(f"""# 搜索结果
id: {id}
result: {search_result}
""", "system"))
        
        result_future = asyncio.Future[list[str]]()
        self.results[id] = result_future
        reply = await result_future

        await self.reply_message(reply, chat, message)


    async def reply_message(self, contents: list[str], chat: Chat, message: HumanMessage | None = None):
        is_first = True
        for msg in contents:
            # 一个字符延迟0.25秒，然后随机抖动0.0-1.0秒
            if not is_first:
                wait_seconds = 0.25 * len(msg) + random.random()
                logger.info(f"waiting {wait_seconds:.2f} seconds...")
                await asyncio.sleep(wait_seconds)
            if is_first and isinstance(message, HumanMessage):
                message.quote(msg)
            else:
                chat.SendMsg(msg)
            logger.info(f"send >> {msg}")
            is_first = False

    
    async def send_message(self, message: BaseMessage, chat: Chat):
        if self.app:
            while True:
                message_count = len(self.send_messages)
                await asyncio.sleep(5)
                if len(self.send_messages) == message_count:
                    break

            event_loop = asyncio.get_running_loop()
            user_msg = f"(发送时间:{datetime.now().strftime("%Y-%m-%d %H:%M")}): {'\n'.join(self.send_messages)}"
            event_loop.create_task(self.app.sync_send_message(user_msg))
            self.future = asyncio.Future[dict[str, typing.Any]]()

            reply: dict[str, typing.Any] = await self.future

            search = reply.get("web_search")
            if search:
                event_loop.create_task(self.search(search, message, chat))

            messages = reply["messages"]
            await self.reply_message(messages, chat)
    
    def on_app_before_initialize(self, app: "Application"):
        self.app = app

    def on_ready(self):
        self.client.wechat_event.add_listen("friend/text,voice,emotion:LIOUA", self.on_wechat_message)
        self.client.wechat_event.add_listen("friend/text,voice,emotion:慕色寒枝", self.on_wechat_message)
    
    def on_message_before_send(self, state: ChatState):
        ...
    
    def on_model_response_completed(self, finish_reason: str):
        logger.info("完成输出")
        reply: dict[str, typing.Any]
        try:
            reply = public_tools.extract_json(self.llm_text)
        except Exception as ex:
            logger.error(f"反序列化json时发生异常喵: {ex}: origin: {self.llm_text}", exc_info=ex)
            return
        finally:
            self.llm_text = ""
        
        search_info = reply.get("web_search")

        if self.future:
            self.future.set_result(reply)
            self.future = None
        elif search_info:
            search_id = search_info.get("id")
            if search_id:
                self.results[search_id].set_result(reply["messages"])

    def on_model_response(self, chunk: ChatCompletionChunk):
        content = chunk.choices[0].delta.content
        self.llm_text += content if content else ""
    
    def emit(self, name: str, arguments: dict):
        if name == "search-result":
            task = self.tasks[arguments["id"]]
            task["future"].set_result(arguments["result"])
