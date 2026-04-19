from concurrent.futures import ThreadPoolExecutor
import asyncio
import typing
import os
import sys

from openai.types.chat import (
    ChatCompletionChunk,
    ChatCompletion
)

from src.components.mcp.mcp_manager import MCPManager
from src.components.ai_chat import AIChat, ChatState
from src.components.plugin_manager.plugin_manager import PluginManager, Hooks, IPCTiming
from src.components.logger.logger import LogCreator
from src.components.app_config import app_config
from src.components.ipc.ipc import IPCServer
from src.components.ipc_handlers.ipc_handler import IPCHandler

logger = LogCreator.instance.create(__name__)
class Application:
    """
    **核心类**

    - 异步事件循环  : 完成度(100%)
    - 触发插件Hooks : 完成度(100%)
    - LLM       : 完成度(100%)
    - MCP       : 模块编写完成，Stdio、StreamableHttp测试成功，OAuth未测试，完成度(90%)
    - Skills    : 完成度(0%) 计划完成MCP后开工
    - 插件管理  : 完成度(100%) 后续计划支持装饰器声明和设置触发顺序
    """
    def __init__(self, args: list[str]):
        # 基础属性
        self.thread_executor = ThreadPoolExecutor(app_config.config["system"].get("thread_workers"))
        self.event_loop = asyncio.new_event_loop()
        # 配置
        self.launch_args: dict[str, str] = Application._parse_args(args)
        self.llm_config = Application._get_llm(app_config.config["llm"]["default"])
        self.default_model = app_config.config["llm"]["default"]
        
        # 组件
        self.plugin_manager = PluginManager()
        self.ai_client: AIChat = Application._load_ai_client_component()
        self.mcp_manager: MCPManager | None = Application._load_mcp_component()
        self.ipc_server: IPCServer | None = self._setup_ipc()
        
        # 全局变量
        self.completed_text = ""
    
    def on_ipc_ready(self):
        self.plugin_manager.trigger("on_ready", "before")
        self.plugin_manager.trigger("on_ready", "after")
        if self.ipc_server:
            handler = IPCHandler(self, self.ipc_server)
            handler.init()

    def on_ipc_error(self, error: Exception):
        logger.error(f"IPC服务启动异常: {error}", exc_info=error)
        sys.exit(1)
    
    def _setup_ipc(self) -> None | IPCServer :
        launch_ipc_uri = self.launch_args.get("ipc_uri")
        ipc_config = app_config.config["system"]["ipc"]
        if launch_ipc_uri is None and not ipc_config.get("enable", False):
            return None
            
        uri = launch_ipc_uri if launch_ipc_uri else ipc_config.get("uri")
        if uri is None:
            raise ValueError("未配置IPC服务地址")
        
        ipc_server = IPCServer(uri)
        ipc_server.on_ipc_ready = self.on_ipc_ready
        ipc_server.on_ipc_error = self.on_ipc_error
        self.event_loop.create_task(ipc_server.start())     # 需要等run_forever启动后才能运行
        return ipc_server
    
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
            "stream": llm_config.get("stream", True)
        }
    
    def exit(self):
        if self.ipc_server:
            self.event_loop.run_until_complete(self.ipc_server.emit("on_app_will_close"))
        self.event_loop.stop()
        logger.info("结束事件循环")
    
    async def run_in_thread(self, func, *args, **kwargs):
        try:
            await self.event_loop.run_in_executor(
                self.thread_executor,
                lambda: func(*args, **kwargs)
            )
        except Exception as ex:
            raise ex

    def initialize(self):
        logger.info("开始初始化应用程序")

        # 异步事件循环
        asyncio.set_event_loop(self.event_loop)
        
        logger.info("初始化插件")
        self.plugin_manager.initialize(app_config.config["plugin_config"])
        logger.info("初始化插件 - OK")

        self.plugin_manager.trigger(
            "on_app_before_initialize",
            "before",
            app = self
            )
        self.plugin_manager.trigger(
            "on_app_before_initialize",
            "after",
            app = self
            )

        # 触发插件对应时机
        self.plugin_manager.trigger(
            "on_app_after_initialized",
            "before"
            )
        self.plugin_manager.trigger(
            "on_app_after_initialized",
            "after"
            )
        logger.info("初始化应用程序完毕")
    
    async def _start_response(self, state: ChatState):
        if state.is_stream:
            try:
                async for chunk in self.ai_client.stream_response(state):
                    self.plugin_manager.trigger(
                        "on_llm_response",
                        "before",
                        chat_completion = chunk
                    )
                    if self.ipc_server:
                        await self.ipc_server.emit(
                            "llm_response",
                            chat_completion = chunk
                        )
                    self.plugin_manager.trigger(
                        "on_llm_response",
                        "after",
                        chat_completion = chunk
                    )

            except Exception as ex:
                logger.info(f"大模型响应时出现异常: {ex}", exc_info=ex)
        else:
            try:
                completion: ChatCompletion = await self.ai_client.non_stream_response(state)
                self.plugin_manager.trigger(
                    "on_llm_response",
                    "before",
                    chat_completion = completion
                )
                if self.ipc_server:
                    await self.ipc_server.emit(
                        "llm_response",
                        chat_completion = completion
                    )
                self.plugin_manager.trigger(
                    "on_llm_response",
                    "after",
                    chat_completion = completion
                )
            except Exception as ex:
                logger.info(f"大模型响应时出现异常: {ex}", exc_info=ex)
        logger.info("大模型响应结束")
    
    async def send_message(self, message: str, msg_type: typing.Literal["user", "system"] = "user"):
        state = self.ai_client.create_state({
            "role": "user",
            "content": [
                    {
                        "type": "text",
                        "text": message
                    }
                ]
            },
            self.llm_config.get("stream", True)
        )
        # 自动注入MCP列表
        if self.mcp_manager and app_config.config["capabilities"]["mcp"]["enable"] and app_config.config["capabilities"]["mcp"]["auto_inject"]:
            state.set_mcp_list(self.mcp_manager.mcp_servers)
        state.msg_type = msg_type
        self.plugin_manager.trigger("on_message_before_send", "before", state=state)
        if self.ipc_server:
            result_state = await self.ipc_server.invoke(
                "message_before_send",
                state = state
            )
            state.change_from_dict(result_state)
        self.plugin_manager.trigger("on_message_before_send", "after", state=state)
        if state.canceled:
            return
        
        logger.info("大模型开始响应")
        self.event_loop.create_task(self._start_response(state))
        self.plugin_manager.trigger("on_message_after_sended", "before", state=state)
        if self.ipc_server:
            await self.ipc_server.emit(
                "on_message_after_sended",
                state = state
            )
        self.plugin_manager.trigger("on_message_after_sended", "after", state=state)

    def run(self):
        try:
            if not self.ipc_server:
                self.plugin_manager.trigger("on_ready", "before")
                self.plugin_manager.trigger("on_ready", "after")
            logger.info("开启事件循环")
            self.event_loop.run_forever()
        except KeyboardInterrupt:
            logger.info("用户已退出")
            self.exit()
            return 0
        except Exception as e:
            logger.error(f"出现异常: {e}")
            return 1
        finally:
            try:
                self.plugin_manager.trigger("on_app_will_close", "before",)
                self.plugin_manager.trigger("on_app_will_close", "after",)
            except Exception as err:
                logger.error(f"出现异常: {err}")
            return 1
        logger.info("主线程退出")
        return 0
