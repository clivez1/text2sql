"""
结构化日志模块

提供统一的 JSON 格式日志输出。
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pathlib import Path

# 尝试导入 python-json-logger
try:
    from pythonjsonlogger.json import JsonFormatter

    HAS_JSON_LOGGER = True
except ImportError:
    JsonFormatter = logging.Formatter
    HAS_JSON_LOGGER = False


class CustomJsonFormatter(JsonFormatter if HAS_JSON_LOGGER else logging.Formatter):
    """自定义 JSON 格式化器"""

    def __init__(self, *args, **kwargs):
        if HAS_JSON_LOGGER:
            super().__init__(*args, **kwargs)
        else:
            super().__init__(*args, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加额外字段
        if hasattr(record, "extra") and record.extra:
            log_data["extra"] = record.extra

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        import json

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = True,
) -> logging.Logger:
    """
    配置结构化日志

    Args:
        level: 日志级别
        log_file: 日志文件路径（可选）
        json_format: 是否使用 JSON 格式

    Returns:
        logging.Logger: 根日志器
    """
    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 创建处理器
    handlers = []

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    handlers.append(console_handler)

    # 文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        handlers.append(file_handler)

    # 设置格式化器
    if json_format and HAS_JSON_LOGGER:
        formatter = CustomJsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    for handler in handlers:
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    获取日志器

    Args:
        name: 日志器名称

    Returns:
        logging.Logger: 日志器实例
    """
    return logging.getLogger(name)


class LogContext:
    """日志上下文管理器"""

    def __init__(self, logger: logging.Logger, **kwargs):
        self.logger = logger
        self.context = kwargs

    def info(self, message: str, **kwargs):
        """记录 INFO 日志"""
        extra = {"extra": {**self.context, **kwargs}}
        self.logger.info(message, extra=extra)

    def error(self, message: str, **kwargs):
        """记录 ERROR 日志"""
        extra = {"extra": {**self.context, **kwargs}}
        self.logger.error(message, extra=extra)

    def warning(self, message: str, **kwargs):
        """记录 WARNING 日志"""
        extra = {"extra": {**self.context, **kwargs}}
        self.logger.warning(message, extra=extra)

    def debug(self, message: str, **kwargs):
        """记录 DEBUG 日志"""
        extra = {"extra": {**self.context, **kwargs}}
        self.logger.debug(message, extra=extra)


# 初始化默认日志配置
def init_app_logging():
    """初始化应用日志"""
    import os

    level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", ".deploy/logs/app.log")
    json_format = os.getenv("LOG_JSON", "true").lower() == "true"

    return setup_logging(
        level=level,
        log_file=log_file,
        json_format=json_format,
    )
