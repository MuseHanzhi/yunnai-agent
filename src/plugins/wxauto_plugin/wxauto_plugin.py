from openai.types.chat import ChatCompletionChunk, ChatCompletion

from src.common import public_tools
from src.plugins.plugin import Plugin
from src.components.logger.logger import LogCreator
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

logger = LogCreator.instance.create(__name__)

class TaskUnit(typing.TypedDict):
    name: str
    message: BaseMessage
    future: asyncio.Future

class WXAutoPlugin(Plugin):
    def __init__(self):
        super().__init__("wechat-plugin")
        self.client: None | WeChatClient = None
        self.app: "Application | None" = None
        self.llm_text = ""
        self.future: asyncio.Future | None = None
        self.send_messages: list[str] = []
        self.handling = False
        self.results: dict[str, asyncio.Future] = {}
        self.hook_registry = [
            "on_app_before_initialize",
            "on_llm_response",
            "on_ready"
        ]
    
    def deinit(self):
        if self.client:
            self.client.Close()
        self.results = {}
        self.send_messages = []
    
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
    
    async def search(self, search_info: dict, message: BaseMessage, chat: Chat):
        if not isinstance(message, HumanMessage) or self.app is None or self.app.mcp_manager is None:
            return
        
        event_loop = asyncio.get_running_loop()
        id: str = search_info["id"]
        activate_ok = True
        if not self.app.mcp_manager.is_activate("WebSearch"):
            try:
                await self.app.mcp_manager.activate("WebSearch")
            except Exception as ex:
                logger.error(f"搜索工具MCP激活失败: {ex}", exc_info=ex)
                activate_ok = False
        
        if activate_ok:
            search_result = await self.app.mcp_manager.call_tool("WebSearch", "bailian_web_search", {
                "query": search_info["keyword"],
                "count": 10
            })
            event_loop.create_task(self.app.sync_send_message(f"""# 搜索结果
id: {id}
result: {search_result["content"]}
""", "system"))
        else:
            event_loop.create_task(self.app.sync_send_message(f"""# 搜索结果
id: {id}
result: 搜索工具激活失败
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
    
    def on_app_before_initialize(self, app: "Application", event_loop: asyncio.AbstractEventLoop):
        self.app = app
        self.client = WeChatClient()
        

    def on_ready(self):
        if not self.client:
            logger.warning("WxAuto客户端为空")
            return
        self.client.wechat_event.add_listen("friend/text,voice,emotion:LIOUA", self.on_wechat_message)
        self.client.wechat_event.add_listen("friend/text,voice,emotion:慕色寒枝", self.on_wechat_message)
    
    def on_llm_response_completed(self):
        reply: dict[str, typing.Any]
        try:
            reply = public_tools.extract_json(self.llm_text)
        except Exception as ex:
            logger.error(f"反序列化json时发生异常喵: {ex}: origin: {self.llm_text}", exc_info=ex)
            return
        finally:
            self.llm_text = ""
        
        web_result_id = reply.get("web_result_id")

        if web_result_id:
            future = self.results.get(web_result_id)
            if future:
                future.set_result(reply["messages"])
        elif self.future:
            self.future.set_result(reply)
            self.future = None

    def on_llm_response(self, chat_completion: "ChatCompletionChunk | ChatCompletion"):
        if not chat_completion.choices:
            logger.warning("大模型响应为空")
            return
        if isinstance(chat_completion, ChatCompletionChunk):
            content = chat_completion.choices[0].delta.content
            self.llm_text += content if content else ""

        elif isinstance(chat_completion, ChatCompletion):
            content = chat_completion.choices[0].message.content
            self.llm_text = content if content else ""
        
        if chat_completion.choices[0].finish_reason:
            self.on_llm_response_completed()
