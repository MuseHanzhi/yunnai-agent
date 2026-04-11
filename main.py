from dotenv import load_dotenv
import sys
import os

from src.components.app_config import app_config
from src.plugins.plugin import Plugin
from src.components.logger.logger import LogCreator
from src.application import Application

def env_check():
    """
    环境检查
    - 检查环境变量
    """
    result = True

    logger.info("开始进行环境检查")
    require_evns: list[str] = app_config.config["system"].get("require_env", [])
    for env_name in require_evns:
        ali_key = os.getenv(env_name)
        if not ali_key:
            result = False
            logger.warning(f"请配置环境变量'{env_name}'")
        logger.info(f"'{env_name}'===OK")
    return result


def main():
    main_app.initialize()
    sys.exit(main_app.run())

load_dotenv()
app_config.load("./app_config.yaml")
LogCreator.instance.load_config(app_config.config["logging"])

logger = LogCreator.instance.create(__name__)
main_app = Application(sys.argv)

if __name__ == '__main__':
    if not env_check():
        sys.exit(1)
    main()
    # test()
