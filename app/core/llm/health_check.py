"""
LLM 健康检测模块

在应用启动时主动检测 LLM API 可用性，避免每次请求被动等待超时。
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class LLMHealthStatus:
    """LLM 健康状态"""
    provider: str
    available: bool
    latency_ms: float
    error: Optional[str] = None
    last_check_time: float = 0.0


class LLMHealthChecker:
    """LLM 健康检测器 - 单例模式"""
    
    _instance: Optional[LLMHealthChecker] = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self._status: Optional[LLMHealthStatus] = None
        self._check_lock = Lock()
    
    def check(self, timeout_seconds: float = 10.0) -> LLMHealthStatus:
        """
        执行 LLM 健康检测
        
        Args:
            timeout_seconds: 检测超时时间
            
        Returns:
            LLMHealthStatus: 健康状态
        """
        with self._check_lock:
            start_time = time.time()
            
            try:
                from app.core.llm.client import get_llm_adapter
                
                # 获取适配器
                adapter = get_llm_adapter()
                provider = adapter.provider_name
                
                logger.info(f"Checking LLM health for provider: {provider}")
                
                # 执行连接检测（带超时）
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"LLM health check timed out after {timeout_seconds}s")
                
                # 设置超时（仅 Unix 系统）
                original_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.setitimer(signal.ITIMER_REAL, timeout_seconds)
                
                try:
                    result = adapter.connectivity_check()
                    signal.setitimer(signal.ITIMER_REAL, 0)
                except TimeoutError:
                    signal.setitimer(signal.ITIMER_REAL, 0)
                    raise
                finally:
                    signal.signal(signal.SIGALRM, original_handler)
                
                latency_ms = (time.time() - start_time) * 1000
                
                # 检测成功
                self._status = LLMHealthStatus(
                    provider=provider,
                    available=True,
                    latency_ms=latency_ms,
                    last_check_time=time.time(),
                )
                
                logger.info(f"LLM health check passed: {provider} ({latency_ms:.0f}ms)")
                return self._status
                
            except TimeoutError as e:
                latency_ms = (time.time() - start_time) * 1000
                self._status = LLMHealthStatus(
                    provider="unknown",
                    available=False,
                    latency_ms=latency_ms,
                    error=str(e),
                    last_check_time=time.time(),
                )
                logger.warning(f"LLM health check timed out: {e}")
                return self._status
                
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                self._status = LLMHealthStatus(
                    provider="unknown",
                    available=False,
                    latency_ms=latency_ms,
                    error=str(e),
                    last_check_time=time.time(),
                )
                logger.warning(f"LLM health check failed: {e}")
                return self._status
    
    def get_status(self) -> Optional[LLMHealthStatus]:
        """获取当前健康状态"""
        return self._status
    
    def is_available(self) -> bool:
        """检查 LLM 是否可用"""
        if self._status is None:
            # 未检测过，执行检测
            status = self.check()
            return status.available
        return self._status.available
    
    def should_use_fallback(self) -> bool:
        """判断是否应该使用 fallback"""
        return not self.is_available()
    
    def reset(self):
        """重置状态"""
        with self._check_lock:
            self._status = None


# 全局单例
_checker: Optional[LLMHealthChecker] = None


def get_llm_health_checker() -> LLMHealthChecker:
    """获取全局健康检测器"""
    global _checker
    if _checker is None:
        _checker = LLMHealthChecker()
    return _checker


def check_llm_health(timeout_seconds: float = 10.0) -> LLMHealthStatus:
    """执行 LLM 健康检测"""
    return get_llm_health_checker().check(timeout_seconds)


def is_llm_available() -> bool:
    """检查 LLM 是否可用"""
    return get_llm_health_checker().is_available()


def should_use_fallback() -> bool:
    """判断是否应该使用 fallback"""
    return get_llm_health_checker().should_use_fallback()
