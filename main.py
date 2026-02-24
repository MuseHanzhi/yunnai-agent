from plugins import (
    ToolsPlugin,
    TTSPlugin,
    ASRPlugin,
    WakeupPlugin
)
from src.components.logger import logger as log
from src.application import Application
import sys

def get_plugin_list():
    plugins = []
    for _, plugin in main_app.plugin_manager.plugins.items():
        plugins.append(str(plugin))
    return {
        "message": "OK",
        "datas": plugins
    }

def set_plugin_state(name: str, state: bool):
    try:
        main_app.plugin_manager.set_plugin_state(name, state)
        logger.info("已打开" if state else "已关闭")
        return {
            "message": "已打开" if state else "已关闭"
        }
    except Exception as e:
        return {
            "message": e
        }

def idle():
    try:
        asr_plugin.emit("stop", {})
        wakeup_plugin.emit("start", {})
    except:
        ...
    return {
        "message": "OK"
        }


def wakeup_handler():
    try:
        asr_plugin.emit("start", {})
    except:
        ...

def speak_end(_text: str):
    try:
        wakeup_plugin.emit("start", {})
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

def main():
    setup_plugins()
    main_app.app_init()
    main_app.run()

logger = log.create(__name__)
wakeup_plugin: WakeupPlugin
asr_plugin: ASRPlugin
main_app = Application(sys.argv)
inner_tools = {
    "plugin_list": get_plugin_list,
    "set_plugin_state": set_plugin_state,
    "idle": idle
}

if __name__ == '__main__':
    main()
    # test()
