import json
from .types import AppConfigOption

def load(config_path: str) -> AppConfigOption:
    try:
        with open(config_path, "r", encoding="utf-8") as fs:
            return json.load(fs)
    except FileNotFoundError:
        raise FileNotFoundError(f"配置文件未找到: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"配置文件格式错误: {config_path}\n详情: {e}")

config = load("app_config.json")
