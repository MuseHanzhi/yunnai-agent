import json
import yaml
from .types import AppConfigOption

def load(config_path: str):
    global config
    try:
        with open(config_path, "r", encoding="utf-8") as fs:
            if config_path.endswith(".json"):
                config = json.load(fs)
            else:
                config = yaml.load(fs, yaml.FullLoader)
    except FileNotFoundError:
        raise FileNotFoundError(f"配置文件未找到: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"配置文件格式错误: {config_path}\n详情: {e}")
    
config: AppConfigOption
