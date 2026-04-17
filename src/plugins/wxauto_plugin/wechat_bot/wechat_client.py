import os
import random
import asyncio
import threading
from datetime import datetime

from mcp.types import TextContent
from openai.types.chat import ChatCompletionContentPartParam
from wxautox4.msgs import (
    BaseMessage,
    TextMessage,
    VoiceMessage,
    EmotionMessage,
    ImageMessage,
    HumanMessage
)
from wxautox4 import WeChat, Chat

from src.common import public_tools
from .wechat_event import WeChatEvent
from src.components.logger.logger import LogCreator
from src.components.ai_chat.chat_state import ChatState

from ..services.oss_service import OSSService
from ..common import tools
from ..types import *

from typing import(
    TypedDict,
    Any,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from src.application import Application

class Message(TypedDict):
    sender: str
    content: str

class TaskUnit(TypedDict):
    name: str
    message: BaseMessage
    future: asyncio.Future

logger = LogCreator.instance.create(__name__)
class WeChatClient(WeChat):
    def __init__(self):
        super().__init__()
        self.wechat_event = WeChatEvent(self)
        self.ready = False
        
        self.config: Config = tools.parse_yaml("./config.yaml")
        self.app: "Application | None" = None
        self.future: asyncio.Future | None = None
        self.oss_service = OSSService(self.config["oss"])
        self.send_messages: list[Message] = []
        self.handling = False
        self.results: dict[str, asyncio.Future] = {}
        self._lock = threading.Lock()
        self.img_urls = []

        # 群员: 消息列表
        self.who_metadata: dict[str, dict] = {}
    
    def deinit(self):
        self.results = {}
        self.send_messages = []

    def llm_completed(self, reply: dict):
        if self.future:
            self.future.set_result(reply)
            self.future = None
    
    def check_env(self) -> bool:
        """
        检查环境变量
        """
        for env_name in self.config["required_env"]:
            if not os.getenv(env_name):
                logger.error(f"环境变量{env_name}未设置")
                return False
        return True
    
    def on_wechat_message(self, message, chat: Chat):
        logger.info(f"接收到{chat.who}的消息: {message}")
        if not isinstance(message, HumanMessage):    
            return
        t_message: Message = {
            "sender": message.sender,
            "content": ""
        }

        if isinstance(message, VoiceMessage):
            text = message.to_text()
            metadata = self.who_metadata.get(chat.who, {"type": "private"})
            chat_type = metadata["type"]
            if chat_type == "group":
                interest_members = metadata.get("interest_members", [])
                if interest_members and message.sender not in interest_members:
                    return
                t_message["content"] = f"<群聊[{chat.who}] 用户: {message.sender}>: {text}"
            else:
                t_message["content"] = text
            # message.click()
        elif isinstance(message, TextMessage):
            text = message.content
            metadata = self.who_metadata.get(chat.who, {"type": "private"})
            chat_type = metadata["type"]
            if chat_type == "group":
                interest_members = metadata.get("interest_members", [])
                if interest_members and message.sender not in interest_members:
                    return
                t_message["content"] = f"<群聊[{chat.who}] 用户: {message.sender}>: {text}"
            else:
                t_message["content"] = text
        elif isinstance(message, EmotionMessage):
            text = f"[发送了一个表情: {message.content}]"
            metadata = self.who_metadata.get(chat.who, {"type": "private"})
            chat_type = metadata["type"]
            if chat_type == "group":
                interest_members = metadata.get("interest_members", [])
                if interest_members and message.sender not in interest_members:
                    return
                t_message["content"] = f"<群聊[{chat.who}] 用户: {message.sender}>: {text}"
            else:
                t_message["content"] = text
        elif isinstance(message, HumanMessage) and message.type == "quote":
            text = message.content
            text = message.content
            metadata = self.who_metadata.get(chat.who, {"type": "private"})
            chat_type = metadata["type"]
            if chat_type == "group":
                interest_members = metadata.get("interest_members", [])
                if interest_members and message.sender not in interest_members:
                    return
                t_message["content"] = f"<群聊[{chat.who}] 用户[{message.sender}] 对 [{message.quote_nickname}] 发送的:{message.quote_content} 进行了回复>: {text}"
            else:
                t_message["content"] = f"<用户[{message.sender}] 对 [{message.quote_nickname}] 发送的:{message.quote_content} 进行了回复>: {text}"
        elif isinstance(message, ImageMessage):
            logger.info("接收到图片消息")
            try:
                res = message.download()
                logger.info(f"下载图片成功: {res}")
            except Exception as e:
                logger.error(f"下载图片失败: {e}", exc_info=e)
                return
            logger.info(f"开始上传图片")
            filename = self.oss_service.upload_file(res)
            if not filename:
                logger.warning("上传图片失败")
                return
            logger.info(f"上传图片成功")
            url = self.oss_service.gerenate_presigned_url(filename)
            self.img_urls.append(url)
            return
        else:
            return
        with self._lock:
            if not self.handling:
                self.handling = True
                self.send_messages.append(t_message)
                # 关键修改：不要在这里 asyncio.run
                # 而是将处理任务提交给 app 的主事件循环
                if self.app and self.app.event_loop:
                    # 使用 run_coroutine_threadsafe 在正确的 loop 中启动协程
                    # 注意：send_message 需要能够访问到当前的 chat 和 message 上下文
                    # 由于 send_message 签名限制，我们可能需要包装一下
                    asyncio.run_coroutine_threadsafe(
                        self._handle_message_flow(message, chat), 
                        self.app.event_loop
                    )
            else:
                self.send_messages.append(t_message)
    async def _handle_message_flow(self, original_message: BaseMessage, chat: Chat):
        """
        在主事件循环中运行的消息处理入口
        """
        try:
            await self.send_message(original_message, chat)
        except Exception as e:
            logger.error(f"处理消息流时发生错误: {e}", exc_info=e)
        finally:
            # 确保状态重置，以便接收下一条消息
            with self._lock:
                self.handling = False
                self.send_messages.clear() # 或者根据需求保留部分历史
    
    async def handle_search_result(self, search_result: str, id, app: "Application", chat: Chat, message: BaseMessage):
        if not app.mcp_manager or not isinstance(message, HumanMessage): return
        
        prompt = f"""
# 搜索结果
id: {id}
{search_result}
"""
        logger.info(f"搜索结果: {search_result}")
        state = app.ai_client.create_state({
            "role": "system",
            "content": prompt
        }, False)
        state.fixed_sys_prompt = tools.read_prompt("chat")
        state.set_extra_body("enable_thinking", False)
        state.messages = app.plugin_manager.emit("session-plugin", "get_chat_records")

        logger.info("开始处理搜索结果")
        response_content = (await app.ai_client.non_stream_response(state)).choices[0].message.content
        logger.info("搜索结果处理完成")

        app.plugin_manager.emit("session-plugin", "add_records", {
            "type": "chat",
            "records": [
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "assistant",
                    "content": response_content
                }
            ]
        })

        reply: dict
        try:
            reply = public_tools.extract_json(response_content)
            await self.reply_message(reply["messages"], chat, message)
        except Exception as ex:
            logger.error(f"解析搜索结果失败: {ex}", exc_info=ex)
            return

    async def search(self, search_info: dict, message: BaseMessage, chat: Chat):
        if not isinstance(message, HumanMessage) or self.app is None or self.app.mcp_manager is None:
            return
        
        activate_ok = self.app.mcp_manager.is_activate("WebSearch")
        if not activate_ok:
            try:
                logger.info("开始激活WebSearch工具MCP")
                await self.app.mcp_manager.activate("WebSearch")
                logger.info("成功激活WebSearch工具MCP")
                activate_ok = True
            except Exception as ex:
                logger.error(f"搜索工具MCP激活失败: {ex}", exc_info=ex)
                activate_ok = False
        
        call_result: str = "工具激活失败"
        if activate_ok:
            search_result = await self.app.mcp_manager.call_tool("WebSearch", "bailian_web_search", {
                "query": search_info["keyword"],
                "count": 3
            })
            content: list[TextContent] = search_result["content"]
            call_result = content[0].text
        await self.handle_search_result(call_result, search_info["id"], self.app, chat, message)
        

    async def reply_message(self, contents: list[str], chat: Chat, message: HumanMessage | None = None):
        is_first = True
        logger.info(f"有{len(contents)}条回复")
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
        if not self.app:
            return

        # 等待消息积累完毕 (5秒内无新消息)
        while True:
            with self._lock:
                message_count = len(self.send_messages)
            await asyncio.sleep(5)
            with self._lock:
                if len(self.send_messages) == message_count:
                    break
            
            # 如果在等待期间 handling 被意外重置（比如出错），则退出
            with self._lock:
                if not self.handling:
                    return

        event_loop = self.app.event_loop
        
        # 获取最终的消息列表快照
        with self._lock:
            current_messages = self.send_messages.copy()
        
        msgs = []
        for item in current_messages:
            if item["content"]:
                msgs.append(item["content"])
        combined_text = '\n'.join(msgs)
        user_msg = f"(发送时间:{datetime.now().strftime('%Y-%m-%d %H:%M')}): {combined_text}"
        
        # 发送消息给 LLM
        event_loop.create_task(self.app.send_message(user_msg))
        
        # 创建 Future 用于接收 LLM 的回复
        # 这个 Future 是在当前 loop (self.app.event_loop) 中创建的，所以可以在下面 await
        self.future = event_loop.create_future()

        try:
            # 这里 await 的是属于当前 event_loop 的 future，不会报错
            reply: dict[str, Any] = await self.future
        except Exception as ex:
            logger.error(f"等待接收信息时出现错误: {ex}", exc_info=ex)
            return

        # 云乃不想回复，直接结束执行
        is_silence = reply.get("silence", False)
        if is_silence:
            logger.info("云乃不想回复")
            return

        search = reply.get("web_search")
        if search:
            event_loop.create_task(self.search(search, message, chat))

        messages = reply.get("messages", [])
        if messages:
            await self.reply_message(messages, chat)
    def on_message_before_send(self, state: ChatState):
        # logger.info(f"发送消息: {state.user_input}")
        state.set_extra_body("enable_thinking", False)
        state.fixed_sys_prompt = tools.read_prompt("chat")
        
        current_message = state.message
        role = current_message["role"]
        if role != "user" or role != "system" or role != "assistant" or role != "developer":
            return

        if self.img_urls:
            content = current_message.get("content", [])

            contents: list[ChatCompletionContentPartParam] = [
                {
                    "type": "image_url",
                    "image_url": url
                }
                for url in self.img_urls
            ]
            
            if content is not None and isinstance(content, str):
                contents.append({
                    "type": "text",
                    "text": content
                })
            
            state.message = {
                "role": role,
                "content": contents
            }

            self.img_urls.clear()

    def setup_listen(self):
        listen_list = self.config.get("listen", [])
        for listen_item in listen_list:
            nickname = listen_item.get("nickname")
            if not nickname:
                continue
            event_type = listen_item.get("event_type")
            if not event_type:
                continue
            msg_types = listen_item.get("msg_types", [])
            event_listener = f"{event_type}/{','.join(msg_types)}:{nickname}"
            self.wechat_event.add_listen(event_listener, self.on_wechat_message)

            self.who_metadata[nickname] = {"type": "private"}
            listen_metadata = listen_item.get("metadata")
            if listen_metadata is None:
                continue
            listen_type = listen_metadata.get("type", "private")
            self.who_metadata[nickname]["type"] = listen_type
            if listen_metadata.get("main_user"):
                self.who_metadata[nickname]["main_user"] = listen_metadata.get("main_user")
            if listen_type == "group":
                self.who_metadata[nickname]["interest_members"] = listen_metadata.get("interest_members", [])
            logger.info(f"监听事件: {event_listener}")

    def init(self, app: "Application"):
        self.app = app
        self.setup_listen()
        self.ready = True

