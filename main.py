import sys
import os

from src.application_tools import application_tools
from src.components.logger import logger as log
from src.application import Application
from plugins import (
    ToolsPlugin,
    TTSPlugin,
    ASRPlugin,
    WakeupPlugin
)

def wakeup_handler():
    try:
        main_app.plugin_manager.emit("wakeup_plugin", "start")
    except:
        ...

def speak_end(_text: str):
    try:
        main_app.plugin_manager.emit("wakeup_plugin", "start")
    except Exception as e:
        logger.error(f"出现错误: {e}")

def asr_ended():
    speak_end("")

def setup_plugins():
    global wakeup_plugin, asr_plugin
    wakeup_plugin = WakeupPlugin(
        "wakeup_plugin",
        ["wakeup_models/nihao-yunnai_zh_windows_v4_0_0.ppn"],
        text="",
        callback=wakeup_handler)
    
    asr_plugin = ASRPlugin("asr_plugin", end_time=3000)
    asr_plugin.bind_speak_end(speak_end)
    asr_plugin.bind_ended(asr_ended)
    
    main_app.add_plugin(
        wakeup_plugin,
        asr_plugin,
        ToolsPlugin("tools_plugin", inner_tool=inner_tools),
        TTSPlugin("tts_plugin")
        )

def env_check():
    """
    环境检查
    - 检查环境变量
    """
    result = True

    logger.info("开始进行环境检查")
    ali_key = os.getenv("DASHSCOPE_API_KEY")
    if not ali_key:
        result = False
        logger.warning("请配置环境变量'DASHSCOPE_API_KEY'")
    logger.info("'DASHSCOPE_API_KEY'===OK")

    por_key = os.getenv("PORCUPINE_ACCESSKEY")
    if not por_key:
        result = False
        logger.warning("请配置环境变量'PORCUPINE_ACCESSKEY'")
    logger.info("'PORCUPINE_ACCESSKEY'===OK")

    return result


def main():
    if not env_check():
        sys.exit(1)
    setup_plugins()
    main_app.app_init()
    sys.exit(main_app.run())

logger = log.create(__name__)
wakeup_plugin: WakeupPlugin
asr_plugin: ASRPlugin
main_app = Application(sys.argv)
inner_tools = {
    "plugin_list": application_tools.get_plugin_list,
    "set_plugin_state": application_tools.set_plugin_state,
    "idle": application_tools.idle
}

if __name__ == '__main__':
    main()
    # test()
