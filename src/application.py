from typing import Any

from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam
import asyncio
import pathlib
import os

from src.core.ui_process import UIProcess
from src.core.ai_chat import AIChat
from src.core.plugin_manager import PluginManager
from src.components.logger import logger as log
from src.core.ipc.ipc import IPCServer
from src.plugins import Plugin
from src.types.message import MessageOptions

logger = log.create(__name__)
class Application:
    """
    **核心类**

    - 事件循环管理
    - 触发Hook插件
    - ipc服务端
    - UI进程
    - LLM管理
    - 插件管理
    """
    def __init__(self, argv):
        self.plugin_manager = PluginManager()
        # AIChat
        logger.info("加载AIChat组件")
        self.ai = AIChat({
            "base_url": os.getenv("LLM_URL", "")
        })
        logger.info("加载AIChat组件完毕")

        self.ui_process = UIProcess()

        self.ipc = IPCServer()

        self._running = False
        self.reply_text = ""
        self.llm_model = "qwen-plus"
    
    def env_check(self):
        # 环境检查
        ...
    
    def close(self, params: dict):
        self._running = False
        if self.event_loop:
            self.event_loop.stop()
            # self.event_loop.close())

    def app_init(self, plugins: list[Plugin] = []):
        logger.info("初始化应用程序")

        self.plugin_manager.add(*plugins)

        self.plugin_manager.trigger(
            "on_app_before_initialize",
            app = self
            )
        
        # 初始化IPC通信
        self.ipc.handle("get-plugins", self.get_plugins)
        self.ipc.handle("set-plugin", self.set_plugin)
        self.ipc.on('send-msg', self.send_msg)
        self.ipc.on('client-ready', self._client_ready)

        self.ai.bind_response_handler(self.on_response)

        # 触发插件对应时机
        self.plugin_manager.trigger("on_app_after_initialized")
        logger.info("初始化应用程序完毕")
    
    def _client_ready(self, params: dict):
        # self._init_ai_chat(params)
        ...
    
    def send_msg(self, params: Any):
        message: MessageOptions = params
        text: str | None = message["data"]["text"]
        
        model_name = message["options"]["model_name"]

        if self.event_loop and message:
            c = self.sync_send_message(model_name, { 'role': 'user', 'content': text })
            self.event_loop.create_task(c)
    
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
    
    def on_response(self, chunk: ChatCompletionChunk | None, finish_reason: str | None):
        if chunk and finish_reason is None:
            self.plugin_manager.trigger(
                "on_model_response",
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
                "on_model_response_completed",
                finish_reason = finish_reason
            )
    
    def _run(self):
        logger.info("初始化事件循环")
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)

        # IPC 服务端
        ipc_host = os.getenv('IPC_HOST')
        ipc_port = os.getenv('IPC_PORT')
        if ipc_host and ipc_port:
            self.ipc.config_server(ipc_host, int(ipc_port))
        self.event_loop.create_task(self.ipc.start(self.event_loop))

        self.plugin_manager.trigger("on_ready")

        # 启动UI进程
        ui_command: str | None = os.getenv('UI_COMMAND')

        if ui_command:
            logger.info("启动UI线程")
            cwd: str | None = os.getenv('UI_CWD')
            ui_process_port: str | None = os.getenv('UI_PORT')
            path = pathlib.Path(os.getcwd(), cwd if cwd else ".")
            self.ui_process.start("yunnai-ui", ui_command, str(path), int(ui_process_port) if ui_process_port else None)

        logger.info("开启事件循环")
        self.event_loop.run_forever()
    
    async def sync_send_message(self, model_name: str | None = None, *messages: ChatCompletionMessageParam):
        await asyncio.sleep(0.01)
        session = self.ai.create_session(model_name if model_name else self.llm_model)
        self.plugin_manager.trigger("on_message_before_send", session=session, messages=messages)
        session.add_messages(*messages)
        self.ai.start_response(session)
        self.plugin_manager.trigger("on_message_after_sended")
    
    def run(self):
        logger.info("开始运行程序")
        try:
            self._run()
        except Exception as e:
            logger.error(f"出现异常: {e}")
            return 1

        try:
            self.plugin_manager.trigger("on_app_will_close")
        except Exception as err:
            logger.error(f"出现异常: {err}")
            return 1
        logger.info("等待后台线程退出")
        logger.info("主线程退出")
        return 0
