"""
弹性 LLM 客户端模块 - Text2SQL 版本

适配 Vanna AI 的弹性调用封装，支持重试、超时控制、降级策略。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError,
)

logger = logging.getLogger(__name__)


@dataclass
class ResilienceConfig:
    """弹性配置"""
    max_retries: int = 3
    timeout_seconds: float = 30.0
    wait_min_seconds: float = 1.0
    wait_max_seconds: float = 10.0
    wait_multiplier: float = 1.0
    fallback_enabled: bool = True
    fallback_sql_template: Optional[str] = None  # 降级 SQL 模板


class ResilientVannaClient:
    """
    弹性 Vanna 客户端
    
    Features:
    - 自动重试（指数退避）
    - 超时控制
    - 降级策略（规则引擎/模板 SQL）
    
    Example:
        >>> client = ResilientVannaClient(vanna_instance=my_vanna)
        >>> sql = client.generate_sql("查询销售额最高的产品")
    """
    
    def __init__(
        self,
        vanna_instance,
        config: Optional[ResilienceConfig] = None,
    ):
        self.vanna = vanna_instance
        self.config = config or ResilienceConfig()
    
    def generate_sql(
        self,
        question: str,
        **kwargs,
    ) -> str:
        """
        生成 SQL（带重试和降级）
        
        Args:
            question: 自然语言问题
            **kwargs: 传递给 Vanna 的其他参数
            
        Returns:
            str: 生成的 SQL
            
        Raises:
            LLMError: 所有重试失败后抛出
        """
        from app.core.errors import LLMError, SQLGenerationError
        
        try:
            return self._generate_sql_with_retry(question, **kwargs)
        except RetryError as e:
            logger.error(f"All retries failed for SQL generation: {e.last_attempt.exception()}")
            return self._handle_sql_failure(question, e.last_attempt.exception() if e.last_attempt else None)
        except (ConnectionError, TimeoutError, OSError) as e:
            logger.error(f"Vanna call failed after retries: {e}")
            return self._handle_sql_failure(question, e)
        except Exception as e:
            logger.exception(f"Unexpected error in Vanna call: {e}")
            raise LLMError(
                message="SQL 生成服务调用失败",
                context={"question": question, "error": str(e)},
            )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _generate_sql_with_retry(self, question: str, **kwargs) -> str:
        """带重试的 SQL 生成（内部方法）"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Vanna call timed out after {self.config.timeout_seconds}s")
        
        original_handler = None
        try:
            # 设置超时（仅 Unix 系统）
            original_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.setitimer(signal.ITIMER_REAL, self.config.timeout_seconds)
            
            result = self.vanna.generate_sql(question, **kwargs)
            
            signal.setitimer(signal.ITIMER_REAL, 0)
            return result
            
        except TimeoutError:
            signal.setitimer(signal.ITIMER_REAL, 0)
            raise
        finally:
            if original_handler is not None:
                signal.signal(signal.SIGALRM, original_handler)
    
    def _handle_sql_failure(self, question: str, original_error: Optional[Exception]) -> str:
        """处理 SQL 生成失败，尝试降级"""
        from app.core.errors import LLMError
        
        # 降级策略 1：使用规则匹配
        if self.config.fallback_enabled:
            fallback_sql = self._try_rule_based_fallback(question)
            if fallback_sql:
                logger.info(f"Using rule-based fallback SQL for question: {question[:50]}...")
                return fallback_sql
        
        # 降级策略 2：使用模板 SQL
        if self.config.fallback_sql_template:
            logger.warning("Using fallback SQL template")
            return self.config.fallback_sql_template
        
        raise LLMError(
            message="SQL 生成服务暂时不可用，请稍后重试",
            detail=f"重试 {self.config.max_retries} 次后仍失败",
            context={
                "question": question,
                "error": str(original_error) if original_error else "Unknown",
            },
        )
    
    def _try_rule_based_fallback(self, question: str) -> Optional[str]:
        """
        基于规则的降级 SQL 生成
        
        简单的关键词匹配，用于 LLM 不可用时提供基础能力。
        """
        question_lower = question.lower()
        
        # 统计类问题
        if any(kw in question_lower for kw in ["多少", "数量", "count"]):
            if "订单" in question_lower:
                return "SELECT COUNT(*) AS count FROM orders LIMIT 10"
            if "产品" in question_lower:
                return "SELECT COUNT(*) AS count FROM products LIMIT 10"
        
        # 排名类问题
        if any(kw in question_lower for kw in ["最高", "top", "排名"]):
            if "销售" in question_lower:
                return """
                    SELECT product_name, SUM(quantity) AS total 
                    FROM order_items 
                    GROUP BY product_name 
                    ORDER BY total DESC 
                    LIMIT 5
                """
        
        # 列表类问题
        if any(kw in question_lower for kw in ["列出", "所有", "哪些"]):
            if "产品" in question_lower:
                return "SELECT * FROM products LIMIT 20"
            if "订单" in question_lower:
                return "SELECT * FROM orders LIMIT 20"
        
        return None
    
    def get_related_ddl(self, question: str, **kwargs) -> List[str]:
        """
        获取相关 DDL（带重试）
        
        Args:
            question: 自然语言问题
            
        Returns:
            List[str]: 相关的 DDL 列表
        """
        from app.core.errors import LLMError
        
        try:
            return self._get_ddl_with_retry(question, **kwargs)
        except Exception as e:
            logger.error(f"Failed to get related DDL: {e}")
            # DDL 获取失败不阻塞，返回空列表
            return []
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
        reraise=True,
    )
    def _get_ddl_with_retry(self, question: str, **kwargs) -> List[str]:
        """带重试的 DDL 获取"""
        return self.vanna.get_related_ddl(question, **kwargs)
    
    def connectivity_check(self) -> bool:
        """检查连接状态"""
        try:
            # 简单测试：尝试获取向量库信息
            self.vanna.get_training_data()
            return True
        except Exception:
            return False


# ============== 全局实例 ==============

_resilient_client: Optional[ResilientVannaClient] = None


def get_resilient_vanna(
    vanna_instance=None,
    config: Optional[ResilienceConfig] = None,
) -> ResilientVannaClient:
    """
    获取弹性 Vanna 客户端
    
    Args:
        vanna_instance: Vanna 实例（默认使用全局配置）
        config: 弹性配置
        
    Returns:
        ResilientVannaClient: 弹性客户端实例
    """
    global _resilient_client
    
    if vanna_instance is None:
        from app.core.llm.vanna_adapter import get_vanna
        vanna_instance = get_vanna()
    
    if _resilient_client is None:
        _resilient_client = ResilientVannaClient(
            vanna_instance=vanna_instance,
            config=config or ResilienceConfig(),
        )
    
    return _resilient_client


def reset_resilient_client() -> None:
    """重置弹性客户端缓存"""
    global _resilient_client
    _resilient_client = None