import logging
import os
from typing import Optional
from .data_file_handler import DataFileHandler

class LogCreator:
    """日志创建器，用于根据配置创建不同级别的日志记录器（单例模式）"""

    _instance = None
    _lock = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._lock = cls._instance._lock = type('Lock', (), {'acquire': lambda: None, 'release': lambda: None})()
        return cls._instance

    @classmethod
    @property
    def instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        # 防止重复初始化
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.default_log_directory = os.path.abspath("logs")
        self._handlers: dict[str, list[logging.Handler]] = {}
        self._filters: list[logging.Filter] = []
        self._initialized = False

    def _create_handler(self, handler_config: dict) -> Optional[logging.Handler]:
        """根据配置创建单个handler"""
        handler_type = handler_config.get("type", "console")
        format_str = handler_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        if handler_type == "console":
            handler = logging.StreamHandler()
        elif handler_type == "file":
            log_path = handler_config.get("log_path", self.default_log_directory)
            filename = handler_config.get("filename", "app.log")
            full_path = os.path.join(log_path, filename)
            encoding = handler_config.get("encoding", "utf-8")
            handler = DataFileHandler(full_path, encoding=encoding)
        else:
            return None

        handler.setFormatter(logging.Formatter(format_str))
        return handler

    def _get_log_level(self, level_name: str) -> int:
        """将日志级别名称转换为logging常量"""
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL
        }
        return level_map.get(level_name.lower(), logging.INFO)

    def load_config(self, logging_config: dict):
        """
        加载日志配置
        Args:
            logging_config: 日志配置字典，从YAML文件加载
        """
        if not logging_config:
            return

        # 清空现有配置
        self._handlers.clear()
        self._filters.clear()

        # 获取handlers配置
        handlers_config = logging_config.get("handlers", {})

        # 为每个级别创建handlers
        for level_name, handler_configs in handlers_config.items():
            level_handlers = []
            for handler_config in handler_configs:
                handler = self._create_handler(handler_config)
                if handler:
                    # 设置handler的日志级别
                    handler.setLevel(self._get_log_level(level_name))
                    level_handlers.append(handler)

            if level_handlers:
                self._handlers[level_name.lower()] = level_handlers

        # 加载filters
        filter_names = logging_config.get("filters", [])
        self._filters = [logging.Filter(name) for name in filter_names if name]

        self._initialized = True

    def create(self, name: str, level: str = "default") -> logging.Logger:
        """
        创建日志记录器
        Args:
            name: 日志记录器名称，通常使用 __name__
            level: 日志级别，可选值: "debug", "info", "warning", "error", "critical", "all", "default"
        Returns:
            配置好的日志记录器实例
        """
        # 如果未初始化，使用默认配置
        if not self._initialized:
            self._setup_default()

        # 创建logger
        logger = logging.getLogger(name)

        # 如果logger已经有handlers，说明已经配置过，直接返回
        if logger.handlers:
            return logger

        # 设置logger级别
        if level == "all":
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(self._get_log_level(level))

        # 添加handlers
        handlers_to_add = []

        # 如果是特定级别，添加该级别的handlers
        if level in self._handlers:
            handlers_to_add.extend(self._handlers[level])
        # 如果是all或default，添加所有级别的handlers
        elif level in ("all", "default"):
            for level_handlers in self._handlers.values():
                handlers_to_add.extend(level_handlers)

        # 添加handlers到logger（去重）
        seen_handlers = set()
        for handler in handlers_to_add:
            handler_id = id(handler)
            if handler_id not in seen_handlers:
                logger.addHandler(handler)
                seen_handlers.add(handler_id)

        # 添加filters
        for filter_obj in self._filters:
            logger.addFilter(filter_obj)

        # 防止日志传播到根logger
        logger.propagate = False

        return logger

    def _setup_default(self):
        """设置默认的日志配置"""
        # 创建默认的console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        console_handler.setLevel(logging.INFO)

        self._handlers["info"] = [console_handler]
        self._initialized = True
