from plugins import (
    LogPlugin,
    ToolsPlugin,
    TTSPlugin,
    ASRPlugin
)
from src.application import Application
import logging
import sys

def asr(state: str):
    asr = main_app.plugins_map.get('asr_plugin', None)
    if asr:
        asr.emit(state, {})
        return {
            "message": "OK"
        }
    else:
        return {
            "message": "失败，没有ASR插件，无法变更更ASR状态"
        }

def close_app():
    main_app.main_window.hide()
    return {
        "message": "OK"
    }

def main():
    main_app.add_plugin(
        LogPlugin("log_plugin"),
        ToolsPlugin("tools_plugin"),
        TTSPlugin("tts_plugin"),
        ASRPlugin("asr_plugin"),
    )
    main_app.app_init()
    main_app.run()

main_app = Application(sys.argv)
inner_tools = {
    "asr": asr,
    "close": close_app
}
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

if __name__ == '__main__':
    main()
