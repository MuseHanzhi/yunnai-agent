from concurrent.futures import ThreadPoolExecutor
import asyncio
import typing
import os

from openai.types.chat import ChatCompletionChunk

from src.components.mcp.mcp_manager import MCPManager
from src.components.ai_chat import AIChat, ChatState
from src.components.plugin_manager import PluginManager
from src.components.logger.logger import LogCreator
from src.components.ipc.ipc import IPCServer
from src.components.ipc_handlers.ipc_handler import IPCHandler
from src.components.app_config import app_config

logger = LogCreator.instance.create(__name__)
class Application:
    """
    **核心类**

    - 异步事件循环  : 完成度(100%)
    - 触发插件Hooks : 完成度(100%)
    - ipc服务 : 完成度(85%)，生命周期hook需要接收结果
    - ipc处理 : 完成度(50%)
    - LLM       : 完成度(100%)
    - MCP       : 模块编写完成，Stdio、StreamableHttp测试成功，OAuth未测试，完成度(90%)
    - Skills    : 计划完成MCP后开工
    - 插件管理  : 完成度(100%)
    """
    def __init__(self, args: list[str]):
        # 配置
        self.launch_args: dict[str, str] = Application._parse_args(args)
        self.llm_config = Application._get_llm(app_config.config["llm"]["default"])
        self.default_model = app_config.config["llm"]["default"]
        
        # 组件
        self.plugin_manager = PluginManager()
        self.ai_client: AIChat = Application._load_ai_client_component()
        self.mcp_manager: MCPManager | None = Application._load_mcp_component()
        self.ipc = IPCServer()
        self.ipc_handler = IPCHandler(self)
        self.thread_executor = ThreadPoolExecutor(app_config.config["system"].get("thread_workers"))
        self.event_loop = asyncio.new_event_loop()
        
        # 全局变量
        self.completed_text = ""
        self.ipc_available = self.launch_args.get("ipc_uri", app_config.config["system"].get("ipc_uri"))
    
    @staticmethod
    def _load_ai_client_component():
        llm_config = Application._get_llm(app_config.config["llm"]["default"])
        logger.info("加载AIChat")
        ai_chat = AIChat({
            "base_url": llm_config["base_url"],
            "api_key": llm_config["api_key"],
            "model_name": llm_config["name"]
        })
        logger.info("加载AIChat完毕")
        return ai_chat
    
    @staticmethod
    def _load_mcp_component():
        mcp_enable = app_config.config["capabilities"]["mcp"].get("enable")
        if mcp_enable:
            logger.info("加载MCP组件")
            mcp_manager = MCPManager()
            mcp_manager.load(
                app_config.config["capabilities"]["mcp"],
                app_config.config["system"]["sys_info"]
            )
            logger.info("加载MCP加载完毕")
            return mcp_manager
        return None
        
    
    @staticmethod
    def _parse_args(args: list[str]):
        temp_args = {}
        for argument in args:
            key_value_pair = argument.split("=")
            if len(key_value_pair) == 2:
                temp_args[key_value_pair[0]] = key_value_pair[1]
            else:
                logger.warning(f"无效的参数: {argument}")
        return temp_args

    @staticmethod
    def _get_llm(model_name: str):
        llm_config = app_config.config["llm"]["models"][model_name]
        api_key = os.getenv(llm_config["key_name"])
        if api_key is None:
            raise ValueError(f"未配置'{llm_config['name']}'密钥，请配置在.env中配置'{llm_config["key_name"]}'密钥")

        return {
            "base_url": llm_config["base_url"],
            "api_key": api_key,
            "name": llm_config["name"],
            "stream": llm_config.get("stream", False)
        }
    
    def exit(self):
        if self.ipc.is_connected:
            self.event_loop.run_until_complete(self.ipc.emit("on_app_will_close"))
            self.event_loop.run_until_complete(self.ipc.close())
        self.event_loop.stop()
        # event_loop.close()
    
    async def run_in_thread(self, func, *args, **kwargs):
        try:
            await self.event_loop.run_in_executor(
                self.thread_executor,
                lambda: func(*args, **kwargs)
            )
        except Exception as ex:
            raise ex
    
    def ipc_ready_handle(self):
        self.event_loop.create_task(self.ipc.emit("on_ready"))
        self.plugin_manager.trigger("on_ready")
        logger.info(f"IPC WebSocket已连接到'{self.ipc.ipc_uri}'")
        logger.info("初始化IPC组件 - OK")

        logger.info("初始化IPC处理函数")
        self.ipc_handler.init()
        logger.info("初始化IPC处理函数 - OK")
    
    def ipc_error_handle(self, ex: Exception):
        self.plugin_manager.trigger("on_ready")
        logger.error("ipc连接失败: {ex}", exc_info=ex)
        logger.error(f"IPC启动失败: {ex}", exc_info=ex)
        logger.info("初始化IPC组件 - FAILED")

    def initialize(self):
        logger.info("开始初始化应用程序")

        # 异步事件循环
        asyncio.set_event_loop(self.event_loop)

        ipc_uri = self.launch_args.get("ipc_uri", app_config.config["system"].get("ipc_uri"))
        if not ipc_uri:
            logger.warning("ipc websocket uri未配置，跳过IPC组件")
        else:
            logger.info("初始化IPC组件")
            self.ipc.on_ipc_ready = self.ipc_ready_handle
            self.ipc.on_ipc_error = self.ipc_error_handle
            self.ipc.initialize(ipc_uri)
            self.event_loop.create_task(self.ipc.start())
        
        logger.info("初始化插件")
        self.plugin_manager.initialize(app_config.config["plugin_config"])
        logger.info("初始化插件 - OK")

        self.plugin_manager.trigger(
            "on_app_before_initialize",
            app = self,
            event_loop = self.event_loop
            )

        # 触发插件对应时机
        self.plugin_manager.trigger(
            "on_app_after_initialized",
            event_loop = self.event_loop
            )
        logger.info("初始化应用程序完毕")
    
    def on_response(self, chunk: ChatCompletionChunk):
        self.plugin_manager.trigger(
                "on_llm_response",
                chunk = chunk
            )
        if self.ipc.is_connected:
            self.event_loop.create_task(self.ipc.emit("on_llm_response", chunk=chunk.model_dump()))
    
    def _start_response(self, state: ChatState):
        if state.is_stream:
            for chunk in self.ai_client.stream_response(state):
                self.on_response(chunk)
        else:
            chunk = self.ai_client.non_stream_response(state)
            self.on_response(chunk)
    
    async def send_message(self, message: str, msg_type: typing.Literal["user", "system"] = "user"):
        state = self.ai_client.create_state(self.llm_config.get("stream", True))    # 默认流式
        state.msg_type = msg_type
        state.user_input = message
        self.plugin_manager.trigger("on_message_before_send", state=state)
        if self.ipc.is_connected:
            await self.ipc.emit("on_message_before_send")
        
        if state.canceled:
            return
        self.event_loop.run_in_executor(None, self._start_response, (state))    # 不要阻塞

        self.plugin_manager.trigger("on_message_after_sended")
        if self.ipc.is_connected:
            await self.ipc.emit("on_message_after_sended")

    def run(self):
        self.initialize()
        try:
            if not self.ipc_available:
                self.plugin_manager.trigger("on_ready")
            logger.info("开启事件循环")
            self.event_loop.run_forever()
        except KeyboardInterrupt:
            self.exit()
            return 0
        except Exception as e:
            logger.error(f"出现异常: {e}")
            return 1
        try:
            self.plugin_manager.trigger("on_app_will_close")
        except Exception as err:
            logger.error(f"出现异常: {err}")
            return 1
        logger.info("主线程退出")
        return 0
