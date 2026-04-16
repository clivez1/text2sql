"""
可观测性模块 - 最小版

提供请求计数、错误率、阶段耗时、trace_id 等可观测性能力。
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict
from threading import Lock
import logging


logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """单个请求的指标"""
    trace_id: str
    endpoint: str
    start_time: float
    end_time: Optional[float] = None
    status: str = "pending"  # pending, success, error
    error_message: Optional[str] = None
    stages: Dict[str, float] = field(default_factory=dict)  # stage_name -> duration_ms


class MetricsCollector:
    """指标收集器 - 单例模式"""
    
    _instance: Optional[MetricsCollector] = None
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
        
        # 请求计数
        self._request_counts: Dict[str, int] = defaultdict(int)
        # 错误计数
        self._error_counts: Dict[str, int] = defaultdict(int)
        # 当前活跃请求
        self._active_requests: Dict[str, RequestMetrics] = {}
        # 已完成请求（保留最近 1000 个）
        self._completed_requests: List[RequestMetrics] = []
        self._max_completed = 1000
        # 阶段耗时统计
        self._stage_durations: Dict[str, List[float]] = defaultdict(list)
        self._stage_counts: Dict[str, int] = defaultdict(int)
    
    def start_request(self, endpoint: str) -> str:
        """开始一个请求，返回 trace_id"""
        trace_id = str(uuid.uuid4())[:8]
        metrics = RequestMetrics(
            trace_id=trace_id,
            endpoint=endpoint,
            start_time=time.time(),
        )
        
        with self._lock:
            self._active_requests[trace_id] = metrics
            self._request_counts[endpoint] += 1
        
        logger.info(f"[trace:{trace_id}] Request started: {endpoint}")
        return trace_id
    
    def end_request(self, trace_id: str, status: str = "success", error_message: Optional[str] = None):
        """结束一个请求"""
        with self._lock:
            metrics = self._active_requests.pop(trace_id, None)
            if not metrics:
                return
            
            metrics.end_time = time.time()
            metrics.status = status
            metrics.error_message = error_message
            
            if status == "error":
                self._error_counts[metrics.endpoint] += 1
            
            self._completed_requests.append(metrics)
            if len(self._completed_requests) > self._max_completed:
                self._completed_requests.pop(0)
        
        duration_ms = (metrics.end_time - metrics.start_time) * 1000
        logger.info(f"[trace:{trace_id}] Request ended: {metrics.endpoint} - {status} ({duration_ms:.2f}ms)")
    
    def record_stage(self, trace_id: str, stage_name: str, duration_ms: float):
        """记录阶段耗时"""
        with self._lock:
            metrics = self._active_requests.get(trace_id)
            if metrics:
                metrics.stages[stage_name] = duration_ms
            
            self._stage_durations[stage_name].append(duration_ms)
            self._stage_counts[stage_name] += 1
            
            # 只保留最近 1000 个
            if len(self._stage_durations[stage_name]) > 1000:
                self._stage_durations[stage_name].pop(0)
        
        logger.debug(f"[trace:{trace_id}] Stage {stage_name}: {duration_ms:.2f}ms")
    
    def get_metrics(self) -> dict:
        """获取所有指标"""
        with self._lock:
            total_requests = sum(self._request_counts.values())
            total_errors = sum(self._error_counts.values())
            
            # 计算各阶段平均耗时
            stage_avg = {}
            for stage, durations in self._stage_durations.items():
                if durations:
                    stage_avg[stage] = {
                        "avg_ms": sum(durations) / len(durations),
                        "count": len(durations),
                    }
            
            return {
                "request_counts": dict(self._request_counts),
                "error_counts": dict(self._error_counts),
                "total_requests": total_requests,
                "total_errors": total_errors,
                "error_rate": total_errors / total_requests if total_requests > 0 else 0,
                "active_requests": len(self._active_requests),
                "stage_metrics": stage_avg,
            }
    
    def reset(self):
        """重置所有指标"""
        with self._lock:
            self._request_counts.clear()
            self._error_counts.clear()
            self._active_requests.clear()
            self._completed_requests.clear()
            self._stage_durations.clear()
            self._stage_counts.clear()


# 全局单例
_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


def start_request(endpoint: str) -> str:
    """开始一个请求"""
    return get_metrics_collector().start_request(endpoint)


def end_request(trace_id: str, status: str = "success", error_message: Optional[str] = None):
    """结束一个请求"""
    get_metrics_collector().end_request(trace_id, status, error_message)


def record_stage(trace_id: str, stage_name: str, duration_ms: float):
    """记录阶段耗时"""
    get_metrics_collector().record_stage(trace_id, stage_name, duration_ms)


def get_metrics() -> dict:
    """获取所有指标"""
    return get_metrics_collector().get_metrics()
