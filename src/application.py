from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam
from threading import Thread
import threading
import asyncio

from .core.ai_chat import AIChat
from plugins import Plugin
from .core.plugin_manager import PluginManager
import src.components.logger as log
from src.core.ipc import IPCServer

logger = log.create(__name__)
class Application:
    """
    **核心类**

    - 事件循环管理
    - 触发Hook插件
    - ipc管理
    - LLM管理
    - 插件管理
    """
    def __init__(self, argv):
        self.plugin_manager = PluginManager()
        # AIChat
        logger.info("加载AIChat组件")
        self.ai = AIChat("qwen-plus")
        self.ai.on_reply = self.on_reply
        logger.info("加载AIChat组件完毕")

        self.ipc = IPCServer()

        self._running = False
        self.reply_text = ""
    
    def add_plugin(self, *plugins: Plugin):
        self.plugin_manager.add(*plugins)
    
    def close(self, params: dict):
        self._running = False
        if self.event_loop:
            self.event_loop.stop()
            # self.event_loop.close())

    def app_init(self):
        logger.info("初始化应用程序")
        self.plugin_manager.trigger(
            "on_app_before_initialize",
            app = self
            )
        
        # 关闭后台程序
        self.ipc.handle("get-plugins", self.get_plugins)
        self.ipc.handle("set-plugin", self.set_plugin)
        self.ipc.on('send-msg', self.send_msg)
        self.ipc.on('client-ready', self._client_ready)

        # 触发插件对应时机
        self.plugin_manager.trigger("on_app_after_initialized")
        logger.info("初始化应用程序完毕")
    
    def _init_ai_chat(self, params: dict):
        arguments = {
            "service_config": {
                "api_key": ""
            },
            "envs": {}
        }
        config: dict = params.get("config", {})
        arguments["service_config"] = config

        envs: dict = params.get("envs", {})
        arguments["envs"] = envs

        try:
            self.ai.init(**arguments)
        except Exception as err:
            logger.error(f"初始化'AIChat'出现异常: {err}")
    
    def _client_ready(self, params: dict):
        self._init_ai_chat(params)
        
    
    def send_msg(self, params: dict):
        message: str | None = params.get("message")
        if self.event_loop and message:
            self.event_loop.create_task(self.sync_send_message({
                'role': 'user',
                'content': message
            }))
    
    def set_plugin(self, params: dict):
        name: str = params.get("name", "")
        state: bool = params.get("state", False)
        try:
            self.plugin_manager.set_plugin_state(name, state)
            return True
        except ValueError as err:
            raise err
    
    def get_plugins(self, params: dict):
        plugins: list[dict] = []
        for n, p in self.plugin_manager.plugins.items():
            plugins.append({
                "name": n,
                "desc": p.desc,
                "version": p.version,
                "state": p.state
            })
        return plugins
    
    def on_send_btn_clicked(self, value: str):
        logger.info(f"user: {value} -> assistant")
        if self.event_loop:
            self.event_loop.create_task(self.sync_send_message({
                "role": "user",
                "content": value
            }))
    
    def on_reply(self, chunk: ChatCompletionChunk | None, finish_reason: str | None):
        if chunk and finish_reason is None:
            self.plugin_manager.trigger(
                "on_ai_reply",
                chunk = chunk
            )

            content = chunk.choices[0].delta.content
            if not content:
                return
            
            self.reply_text += content
            if self.event_loop:
                try:
                    self.event_loop.create_task(self.ipc.emit("ai-response", message = content)).result()
                except:
                    ...

        elif not finish_reason is None:
            self.reply_text = ""
            if self.event_loop:
                self.event_loop.create_task(self.ipc.emit("ai-response-completed"))
            self.plugin_manager.trigger(
                "on_ai_reply_completed",
                finish_reason = finish_reason
            )
    
    # async def run_task(self):
    #     ...
        
    
    def _run(self):
        threading.current_thread().name = 'background_thread'
        logger.info("初始化")

        logger.info("初始化事件循环")
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.create_task(self.ipc.start(self.event_loop))

        self.plugin_manager.trigger("on_background_thread_start")

        logger.info("开启事件循环")
        self.event_loop.run_forever()

        self.plugin_manager.trigger("on_background_thread_end")
    
    async def sync_send_message(self, *messages: ChatCompletionMessageParam):
        await asyncio.sleep(0.01)
        self.send_message(*messages)
    
    def send_message(self, *messages: ChatCompletionMessageParam):
        session = self.ai.create_session()
        self.plugin_manager.trigger("on_message_before_send", session=session, messages=messages)
        session.add_messages(*messages)
        self.ai.start_response(session)
        self.plugin_manager.trigger("on_message_after_sended")
    
    def delay_close(self, seconds: int):
         if seconds > 2:
              return False
         return True
    
    def run(self):
        logger.info("开始运行程序")
        self._run()

        self.plugin_manager.trigger("on_app_will_close", delay_request = self.delay_close)
        logger.info("等待后台线程退出")
        logger.info("主线程退出")
