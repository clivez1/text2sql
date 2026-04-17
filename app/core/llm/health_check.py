"""
LLM 健康检测模块

在应用启动时主动检测 LLM API 可用性，避免每次请求被动等待超时。
支持多模型检测（index=1..N）。
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class LLMHealthStatus:
    """LLM 健康状态"""

    provider: str
    available: bool
    latency_ms: float
    error: Optional[str] = None
    last_check_time: float = 0.0
    index: int = 1


class LLMHealthChecker:
    """LLM 健康检测器 - 单例模式"""

    _instance: Optional[LLMHealthChecker] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 存储每个 index 的健康状态
        self._statuses: dict[int, LLMHealthStatus] = {}
        self._check_lock = threading.Lock()

    def check(self, index: int = 1, timeout_seconds: float = 10.0) -> LLMHealthStatus:
        """
        执行 LLM 健康检测（单模型）

        Args:
            index: 模型索引（1=primary, 2=fallback, ...）
            timeout_seconds: 检测超时时间

        Returns:
            LLMHealthStatus: 健康状态
        """
        from app.core.llm.client import get_llm_adapter
        from app.config.settings import get_settings

        settings = get_settings()

        # 使用 settings 验证 index 并获取配置
        try:
            config = settings.get_provider_config(index)
        except ValueError:
            # Index out of range
            status = LLMHealthStatus(
                provider="none",
                available=False,
                latency_ms=0,
                error=f"Provider index={index} not configured",
                last_check_time=time.time(),
                index=index,
            )
            self._statuses[index] = status
            return status

        if not config.api_key:
            status = LLMHealthStatus(
                provider="none",
                available=False,
                latency_ms=0,
                error=f"No API key for index={index}",
                last_check_time=time.time(),
                index=index,
            )
            self._statuses[index] = status
            return status

        start_time = time.time()

        try:
            adapter = get_llm_adapter(index)
            provider = adapter.provider_name
            logger.info(f"Checking LLM health for provider: {provider} (index={index})")

            # 使用线程超时（兼容 Windows）
            result_holder = [None]
            error_holder = [None]

            def target():
                try:
                    result_holder[0] = adapter.connectivity_check()
                except Exception as e:
                    error_holder[0] = e

            t = threading.Thread(target=target, daemon=True)
            t.start()
            t.join(timeout=timeout_seconds)

            if t.is_alive():
                raise TimeoutError(
                    f"LLM health check timed out after {timeout_seconds}s"
                )

            if error_holder[0]:
                raise error_holder[0]

            result = result_holder[0]
            latency_ms = (time.time() - start_time) * 1000

            status = LLMHealthStatus(
                provider=provider,
                available=True,
                latency_ms=latency_ms,
                last_check_time=time.time(),
                index=index,
            )
            self._statuses[index] = status
            logger.info(
                f"LLM health check passed: {provider} ({latency_ms:.0f}ms) [index={index}]"
            )
            return status

        except TimeoutError as e:
            latency_ms = (time.time() - start_time) * 1000
            status = LLMHealthStatus(
                provider="unknown",
                available=False,
                latency_ms=latency_ms,
                error=str(e),
                last_check_time=time.time(),
                index=index,
            )
            self._statuses[index] = status
            logger.warning(f"LLM health check timed out [index={index}]: {e}")
            return status

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            status = LLMHealthStatus(
                provider="unknown",
                available=False,
                latency_ms=latency_ms,
                error=str(e),
                last_check_time=time.time(),
                index=index,
            )
            self._statuses[index] = status
            logger.warning(f"LLM health check failed [index={index}]: {e}")
            return status

    def get_status(self, index: int = 1) -> Optional[LLMHealthStatus]:
        """获取当前健康状态"""
        return self._statuses.get(index)

    def is_available(self, index: int = 1) -> bool:
        """检查指定 index 的 LLM 是否可用"""
        status = self._statuses.get(index)
        if status is None:
            status = self.check(index)
        return status.available if status else False

    def should_use_fallback(self) -> bool:
        """Primary (index=1) is unavailable."""
        return not self.is_available(index=1)

    def reset(self, index: Optional[int] = None):
        """重置状态"""
        if index is None:
            self._statuses.clear()
        else:
            self._statuses.pop(index, None)


# 全局单例
_checker: Optional[LLMHealthChecker] = None


def get_llm_health_checker() -> LLMHealthChecker:
    """获取全局健康检测器"""
    global _checker
    if _checker is None:
        _checker = LLMHealthChecker()
    return _checker


def check_llm_health(index: int = 1, timeout_seconds: float = 10.0) -> LLMHealthStatus:
    """执行 LLM 健康检测"""
    return get_llm_health_checker().check(index, timeout_seconds)


def is_llm_available(index: int = 1) -> bool:
    """检查 LLM 是否可用"""
    return get_llm_health_checker().is_available(index)


def should_use_fallback() -> bool:
    """判断是否应该使用 fallback"""
    return get_llm_health_checker().should_use_fallback()


def check_all_providers(timeout_seconds: float = 10.0) -> list[LLMHealthStatus]:
    """Check health of all configured providers."""
    from app.config.settings import get_settings

    checker = get_llm_health_checker()
    settings = get_settings()
    return [
        checker.check(i, timeout_seconds) for i in range(1, settings.provider_count + 1)
    ]
