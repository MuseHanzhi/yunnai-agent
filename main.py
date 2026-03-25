from dotenv import load_dotenv
import sys
import os

from src.plugins.plugin import Plugin
from src.components.logger import logger as log
from src.application import Application
from src.plugins import (
    TTSPlugin,
)
def setup_plugins() -> list[Plugin]:
    
    return [
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
    main_app.app_init()
    sys.exit(main_app.run())

load_dotenv()

logger = log.create(__name__)
main_app = Application(sys.argv)
env_names: list[str] = [
    "DASHSCOPE_API_KEY",
    "PORCUPINE_ACCESSKEY"
]

if __name__ == '__main__':
    if not env_check():
        sys.exit(1)
    main()
    # test()
