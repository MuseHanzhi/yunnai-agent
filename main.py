from dotenv import load_dotenv
import sys
import os

from src.plugins.plugin import Plugin
from src.application_tools import application_tools
from src.components.logger import logger as log
from src.application import Application
from src.plugins import (
    ToolsPlugin,
    TTSPlugin,
)

#region
# def wakeup_handler():
#     try:
#         main_app.plugin_manager.emit("wakeup_plugin", "start")
#     except:
#         ...

# def speak_end(_text: str):
#     try:
#         main_app.plugin_manager.emit("wakeup_plugin", "start")
#     except Exception as e:
#         logger.error(f"出现错误: {e}")

# def asr_ended():
#     speak_end("")
#endregion

def setup_plugins() -> list[Plugin]:
    #region
    # global wakeup_plugin, asr_plugin
    # wakeup_plugin = WakeupPlugin(
    #     "wakeup_plugin",
    #     ["wakeup_models/nihao-yunnai_zh_windows_v4_0_0.ppn"],
    #     text="",
    #     callback=wakeup_handler)
    
    # asr_plugin = ASRPlugin("asr_plugin", end_time=3000)
    # asr_plugin.bind_speak_end(speak_end)
    # asr_plugin.bind_ended(asr_ended)
    #endregion
    
    return [
        # wakeup_plugin,
        # asr_plugin,
        ToolsPlugin("tools_plugin", inner_tool=inner_tools),
        TTSPlugin("tts_plugin")
    ]

def env_check():
    """
    环境检查
    - 检查环境变量
    """
    result = True

    logger.info("开始进行环境检查")

    for env_name in env_names:
        ali_key = os.getenv(env_name)
        if not ali_key:
            result = False
            logger.warning(f"请配置环境变量'{env_name}'")
        logger.info(f"'{env_name}'===OK")

    return result


def main():
    if not env_check():
        sys.exit(1)

    main_app.app_init(setup_plugins())
    sys.exit(main_app.run())

load_dotenv()
logger = log.create(__name__)
#region
# wakeup_plugin: WakeupPlugin
# asr_plugin: ASRPlugin
#endregion
main_app = Application(sys.argv)
env_names: list[str] = [
    "DASHSCOPE_API_KEY",
    "PORCUPINE_ACCESSKEY"
]
inner_tools = {
    "plugin_list": application_tools.get_plugin_list,
    "set_plugin_state": application_tools.set_plugin_state,
    "idle": application_tools.idle
}

if __name__ == '__main__':
    main()
    # test()
