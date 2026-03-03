from src.application import Application
from src.components.logger import logger as logging

logger = logging.create(__name__)

_instance: None | Application = None

def set_app(app: Application):
    global _instance
    if not _instance:
        _instance = app


def get_plugin_list():
    if not _instance:
        return {
            "message": "error: 'application' is not ready"
        }
    
    plugins = []
    for _, plugin in _instance.plugin_manager.items():
        plugins.append(str(plugin))
    return {
        "message": "OK",
        "datas": plugins
    }

def set_plugin_state(name: str, state: bool):
    if not _instance:
        return {
            "message": "error: 'application' is not ready"
        }

    try:
        _instance.plugin_manager.set_plugin_state(name, state)
        logger.info("已打开" if state else "已关闭")
        return {
            "message": "已打开" if state else "已关闭"
        }
    except Exception as e:
        return {
            "message": e
        }

def idle():
    if not _instance:
        return {
            "message": "error: 'application' is not ready"
        }
    
    try:
        _instance.plugin_manager.emit("asr_plugin", "stop")
        _instance.plugin_manager.emit("wakeup_plugin", "start")
    except:
        ...
    return {
        "message": "OK"
        }
