from plugins import (
    LogPlugin,
    ToolsPlugin,
    TTSPlugin,
    ASRPlugin,
    WakeupPlugin
)
from src.application import Application
import logging
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
        logging.info("已打开" if state else "已关闭")
        return {
            "message": "已打开" if state else "已关闭"
        }
    except Exception as e:
        return {
            "message": e
        }

def idle():
    try:
        main_app.plugin_manager.emit("asr_plugin", "stop")
        main_app.plugin_manager.emit("wakeup_plugin", "start")
    except:
        ...
    return {
        "message": "OK"
        }


def wakeup_handler():
    main_app.plugin_manager.emit("asr_plugin", "start")

def setup_plugins():
    wakeup = WakeupPlugin(
        "wakeup_plugin",
        ["wakeup_models/nihao-yunnai_zh_windows_v4_0_0.ppn"],
        text="",
        callback=wakeup_handler)
    
    main_app.add_plugin(
        # wakeup,
        LogPlugin("log_plugin"),
        ToolsPlugin("tools_plugin", inner_tool=inner_tools),
        # TTSPlugin("tts_plugin"),
        # ASRPlugin("asr_plugin", False)
        )

def main():
    setup_plugins()
    main_app.app_init()
    main_app.run()

main_app = Application(sys.argv)
inner_tools = {
    "plugin_list": get_plugin_list,
    "set_plugin_state": set_plugin_state,
    "idle": idle
}
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

if __name__ == '__main__':
    main()
