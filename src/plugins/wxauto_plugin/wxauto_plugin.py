import typing
import asyncio

from openai.types.chat import ChatCompletionChunk, ChatCompletion

from src.components.ai_chat.chat_state import ChatState
from src.common import public_tools
from src.plugins.plugin import Plugin
from src.components.logger.logger import LogCreator
from .wechat_bot.wechat_client import WeChatClient
from src.plugins.hook_registry import registry

if typing.TYPE_CHECKING:
    from src.application import Application

logger = LogCreator.instance.create(__name__)

class WXAutoPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client: None | WeChatClient = None
        self.llm_text = ""
        self.app: "Application | None" = None
    
    @registry.on_app_before_initialize()
    def on_app_before_initialize(self, app: "Application"):
        self.app = app
        self.client = WeChatClient()

    @registry.on_ready()
    def on_ready(self):
        if not self.client or not self.app:
            logger.warning("WxAuto客户端或者主程序为空")
            return
        self.client.init(self.app)
    
    def deinit(self):
        self.deinit()
        if self.client:
            self.client.Close()
    
    def llm_end_handle(self):
        if not self.client or not self.client.ready:
            return
        reply: dict[str, typing.Any]
        try:
            reply = public_tools.extract_json(self.llm_text)
            self.client.llm_completed(reply)
        except Exception as ex:
            logger.error(f"反序列化json时发生异常喵: {ex}: origin: {self.llm_text}", exc_info=ex)
            return
        finally:
            self.llm_text = ""
    
    @registry.on_message_before_send()
    def on_message_before_send(self, state: ChatState):
        if not self.client or not self.client.ready:
            return
        self.client.on_message_before_send(state)

    @registry.on_llm_response()
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
            self.llm_end_handle()
