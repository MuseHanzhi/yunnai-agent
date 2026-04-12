from dotenv import load_dotenv
import sys
import os

from src.components.app_config import app_config
from src.components.logger.logger import LogCreator
from src.application import Application

def env_check():
    """
    环境检查
    - 检查环境变量
    """
    result = True

    logger.info("开始系统环境检查")
    require_evns: list[str] = app_config.config["system"].get("require_env", [])
    for env_name in require_evns:
        env_value = os.getenv(env_name)
        if not env_value:
            result = False
            logger.warning(f"[{env_name}] === FAIL")
            continue
        logger.info(f"[{env_name}] === PASS")
    return result

def main():
    if not env_check():
        logger.error("系统环境检查失败")
        sys.exit(1)
    main_app = Application(sys.argv[1:])
    sys.exit(main_app.run())
    
load_dotenv()

app_config.load("./app_config.yaml")
LogCreator.instance.load_config(app_config.config["logging"])

logger = LogCreator.instance.create(__name__)

if __name__ == '__main__':
    main()
    
