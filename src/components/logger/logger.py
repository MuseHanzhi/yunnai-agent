import logging
import json
from typing import Any
import os
from src.components.logger.data_file_handler import DataFileHandler

default_log_directory = os.path.abspath("logs")

_handlers: dict[str, list[logging.Handler]] = {}
_filters: list[logging.Filter] = []

def add_handler(*handles: logging.Handler):
    add_handler_for_level("all", *handles)

def add_handler_for_level(level: str, *handles: logging.Handler):
    temp_handlers = _handlers.get(level)
    if temp_handlers:
        temp_handlers.append(*handles)
    else:
        _handlers[level] = list(handles)

def add_filter(*filters: logging.Filter):
    global _filters
    if not _filters:
        _filters = list(filters)
        return
    _filters.append(*filters)
    
def create(name: str, level = "all"):
    logger = logging.Logger(name, level if level != "all" else 0)
    for handle in _handlers.get(level, []):
        logger.addHandler(handle)

    for filter in _filters:
        logger.addFilter(filter)

    return logger

def load_config(config_path):
    global _filters

    if not os.path.exists(config_path):
        return

    config: dict
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    logging_section: dict = config.get("logging", {})
    if not logging_section:
        return
    levels: dict[str, Any] = logging_section.get("handlers", {})
    default_log_path = os.path.join(default_log_directory, ".log")
    for level, item in levels.items():
        handles: list[logging.Handler] = []
        for c in item:
            type: str = c.get("type", "info")
            format = c.get("format", "")
            handle: logging.Handler | None = None
            if type == "console":   # 控制台输出
                handle = logging.StreamHandler()
                handle.setFormatter(logging.Formatter(format))
            elif type == "file":    # 文件输出
                filename = c.get("filename", default_log_path)
                encoding = c.get("encoding", "utf-8")
                handle = DataFileHandler(filename, encoding=encoding)
                handle.setFormatter(logging.Formatter(format))
            if handle:
                handles.append(handle)
        _handlers[level.upper()] = handles
        _handlers["all"] = handles
    
    filter_names: list[str] = logging_section.get("filters", [])
    _filters = [logging.Filter(name) for name in filter_names if name]

load_config("app_config.json")

__all__ = [
    "create",
    "add_handler",
    "add_handler_for_level",
    "add_filter",
    "load_config"
]