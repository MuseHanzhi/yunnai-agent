import asyncio
import typing
import os

from openai.types.chat import ChatCompletionChunk

from src.components.mcp.mcp_manager import MCPManager
from src.common import prompt_tools
from src.components.ai_chat import AIChat
from src.components.plugin_manager import PluginManager
from src.components.logger.logger import LogCreator
from src.components.ipc.ipc import IPCServer
from src.components.ipc_handlers.ipc_handler import IPCHandler
from src.components.app_config import app_config

logger = LogCreator.instance.create(__name__)
class Application:
    """
    **核心类**

    - 运行事件循环  : 完成度(100%)
    - 触发插件Hooks : 完成度(100%)
    - ipc服务端 : 完成度(100%)
    - ipc处理 : 完成度(50%)
    - LLM       : 完成度(100%)
    - MCP       : 模块编写完成，Stdio、StreamableHttp测试成功，OAuth未测试，完成度(90%)
    - Skills    : 计划完成MCP后开工
    - 插件管理  : 完成度(100%)
    """
    def __init__(self, args):
        self.plugin_manager = PluginManager(app_config.config["plugin_config"])
        # AIChat
        logger.info("加载AIChat")
        self.llm_config = Application._get_llm(app_config.config["llm"]["default"])
        self.default_model = app_config.config["llm"]["default"]
        self.ai_client = AIChat({
            "base_url": self.llm_config["base_url"],
            "api_key": self.llm_config["api_key"],
            "model_name": self.llm_config["name"]
        })
        logger.info("加载AIChat完毕")

        mcp_enable = app_config.config["capabilities"]["mcp"].get("enable")
        self.mcp_manager: MCPManager | None = None
        if mcp_enable:
            logger.info("加载MCP组件")
            self.mcp_manager = MCPManager()
            self.mcp_manager.load(
                app_config.config["capabilities"]["mcp"],
                {
                    "name": "yunnai",
                    "version": "1.0.0"
                }
            )
            logger.info("加载MCP加载完毕")

        self.ipc = IPCServer()
        self.ipc_handler = IPCHandler(self)

        self.completed_text = ""
        self.is_ready = False
        self.prompts: dict[str, str] = {}
        self.end_line = ""
    

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
            "stream": llm_config
        }
    
    def close(self):
        event_loop = asyncio.get_event_loop()
        if event_loop:
            event_loop.stop()
            # event_loop.close()

    def initialize(self):
        logger.info("初始化应用程序")

        # 异步事件循环
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)

        self.ipc_handler.init()
        self.plugin_manager.init_plugin()

        self.plugin_manager.trigger(
            "on_app_before_initialize",
            app = self,
            event_loop = event_loop
            )

        self.ai_client.bind_response_handler(self.on_response)

        # 触发插件对应时机
        self.plugin_manager.trigger(
            "on_app_after_initialized",
            event_loop = event_loop
            )
        logger.info("初始化应用程序完毕")
    
    def on_response(self, chunk: ChatCompletionChunk | None, finish_reason: str | None):
        event_loop = asyncio.get_event_loop()
        if chunk and finish_reason is None:
            self.plugin_manager.trigger(
                "on_llm_response",
                chunk = chunk
            )

            content = chunk.choices[0].delta.content
            if not content:
                return
            self.completed_text += content

            try:
                event_loop.create_task(self.ipc.emit(None, "on_llm_response", message = content)).result()
            except asyncio.exceptions.InvalidStateError:
                ...
            except Exception as ex:
                logger.error(f"触发ipc事件时发异常: {ex}", exc_info=ex)

        elif not finish_reason is None:
            event_loop.create_task(self.ipc.emit(None, "on_llm_response_completed"))
            self.plugin_manager.trigger(
                "on_llm_response_completed",
                finish_reason = finish_reason
            )
            self.completed_text = ""


    def _run(self):
        # IPC 服务端
        ipc_host = app_config.config["system"]["ipc_server"]["host"]
        ipc_port = app_config.config["system"]["ipc_server"]["port"]
        if ipc_host and ipc_port:
            self.ipc.config_server(ipc_host, ipc_port)
        
        event_loop = asyncio.get_event_loop()
        event_loop.create_task(self.ipc.start())
        event_loop.create_task(self.ipc.emit(None, "ready"))
        self.plugin_manager.trigger("on_ready")

        logger.info("开启事件循环")
        event_loop.run_forever()
    
    async def sync_send_message(self, message: str, msg_type: typing.Literal["user", "system"] = "user"):
        state = self.ai_client.create_state()
        state.fixed_sys_prompt = prompt_tools.read_prompt("chat")
        state.msg_type = msg_type
        state.user_input = message
        self.plugin_manager.trigger("on_message_before_send", state=state)
        await self.ipc.emit(None, "on_message_before_send")
        if state.type == "agent":
            await self.ipc.emit(None, "agent-mode", task_name=message)
        if state.canceled:
            return
        self.ai_client.start_response(state)
        self.plugin_manager.trigger("on_message_after_sended")
        await self.ipc.emit(None, "on_message_after_sended")

    def run(self):
        logger.info("开始运行程序")
        try:
            self._run()
        except Exception as e:
            logger.error(f"出现异常: {e}")
            return 1
        try:
            asyncio.run(self.ipc.emit(None, "on_app_will_close"))
            self.plugin_manager.trigger("on_app_will_close")
        except Exception as err:
            logger.error(f"出现异常: {err}")
            return 1
        logger.info("等待后台线程退出")
        logger.info("主线程退出")
        return 0
