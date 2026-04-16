"""
可观测性模块测试
"""
import pytest
import time

from app.core.metrics import (
    MetricsCollector,
    get_metrics_collector,
    start_request,
    end_request,
    record_stage,
    get_metrics,
)


class TestMetricsCollector:
    """指标收集器测试"""
    
    def test_singleton(self):
        """测试单例模式"""
        collector1 = MetricsCollector()
        collector2 = MetricsCollector()
        assert collector1 is collector2
    
    def test_get_metrics_collector(self):
        """测试获取全局收集器"""
        collector = get_metrics_collector()
        assert collector is not None
        assert isinstance(collector, MetricsCollector)
    
    def test_start_request(self):
        """测试开始请求"""
        collector = MetricsCollector()
        collector.reset()
        
        trace_id = collector.start_request("/ask")
        
        assert trace_id is not None
        assert len(trace_id) == 8
        assert collector._request_counts["/ask"] == 1
    
    def test_end_request_success(self):
        """测试结束请求 - 成功"""
        collector = MetricsCollector()
        collector.reset()
        
        trace_id = collector.start_request("/ask")
        collector.end_request(trace_id, "success")
        
        assert collector._error_counts["/ask"] == 0
        assert len(collector._completed_requests) == 1
    
    def test_end_request_error(self):
        """测试结束请求 - 错误"""
        collector = MetricsCollector()
        collector.reset()
        
        trace_id = collector.start_request("/ask")
        collector.end_request(trace_id, "error", "Test error")
        
        assert collector._error_counts["/ask"] == 1
        assert len(collector._completed_requests) == 1
    
    def test_record_stage(self):
        """测试记录阶段耗时"""
        collector = MetricsCollector()
        collector.reset()
        
        trace_id = collector.start_request("/ask")
        collector.record_stage(trace_id, "pipeline", 100.5)
        
        assert "pipeline" in collector._stage_durations
        assert collector._stage_durations["pipeline"][0] == 100.5
    
    def test_get_metrics(self):
        """测试获取指标"""
        collector = MetricsCollector()
        collector.reset()
        
        # 发送几个请求
        trace_id1 = collector.start_request("/ask")
        collector.end_request(trace_id1, "success")
        
        trace_id2 = collector.start_request("/ask")
        collector.end_request(trace_id2, "error", "Test error")
        
        metrics = collector.get_metrics()
        
        assert metrics["total_requests"] == 2
        assert metrics["total_errors"] == 1
        assert metrics["error_rate"] == 0.5
        assert metrics["request_counts"]["/ask"] == 2
        assert metrics["error_counts"]["/ask"] == 1
    
    def test_reset(self):
        """测试重置"""
        collector = MetricsCollector()
        
        trace_id = collector.start_request("/ask")
        collector.end_request(trace_id, "success")
        
        collector.reset()
        
        assert collector._request_counts["/ask"] == 0
        assert len(collector._completed_requests) == 0


class TestConvenienceFunctions:
    """便捷函数测试"""
    
    def test_start_request_function(self):
        """测试 start_request 函数"""
        collector = get_metrics_collector()
        collector.reset()
        
        trace_id = start_request("/health")
        
        assert trace_id is not None
        assert collector._request_counts["/health"] == 1
    
    def test_end_request_function(self):
        """测试 end_request 函数"""
        collector = get_metrics_collector()
        collector.reset()
        
        trace_id = start_request("/health")
        end_request(trace_id, "success")
        
        assert len(collector._completed_requests) == 1
    
    def test_record_stage_function(self):
        """测试 record_stage 函数"""
        collector = get_metrics_collector()
        collector.reset()
        
        trace_id = start_request("/ask")
        record_stage(trace_id, "chart", 50.0)
        
        assert "chart" in collector._stage_durations
    
    def test_get_metrics_function(self):
        """测试 get_metrics 函数"""
        collector = get_metrics_collector()
        collector.reset()
        
        trace_id = start_request("/ask")
        record_stage(trace_id, "pipeline", 100.0)
        end_request(trace_id, "success")
        
        metrics = get_metrics()
        
        assert metrics["total_requests"] == 1
        assert "pipeline" in metrics["stage_metrics"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
