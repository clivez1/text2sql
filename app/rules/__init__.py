"""
规则存储模块 - 从 YAML 加载规则

提供 RuleStore 类，从 default_rules.yaml 加载规则列表。
"""
from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import yaml


@dataclass(frozen=True)
class Rule:
    """一条规则"""
    keywords: tuple[str, ...]
    sql: str
    explanation: str
    priority: int = 0
    tags: tuple[str, ...] = ()


class RuleStore:
    """规则仓库，从 YAML 加载并匹配"""

    _instance: Optional["RuleStore"] = None

    def __init__(self, rules: list[Rule]):
        self._rules = rules

    @classmethod
    def get_instance(cls) -> "RuleStore":
        """获取单例实例（延迟加载）"""
        if cls._instance is None:
            cls._instance = cls._load()
        return cls._instance

    @classmethod
    def _load(cls) -> "RuleStore":
        """从 YAML 文件加载规则"""
        rules_path = Path(__file__).parent / "default_rules.yaml"
        if not rules_path.exists():
            raise FileNotFoundError(f"规则文件不存在: {rules_path}")

        with open(rules_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        rules: list[Rule] = []
        for item in data.get("rules", []):
            keywords = tuple(item["keywords"])
            rules.append(
                Rule(
                    keywords=keywords,
                    sql=item["sql"],
                    explanation=item["explanation"],
                    priority=item.get("priority", 0),
                    tags=tuple(item.get("tags", [])),
                )
            )
        return cls(rules)

    def match(self, normalized: str) -> Optional[tuple[str, str]]:
        """
        匹配规则，返回 (sql, explanation)。

        匹配逻辑：all(kw in normalized for kw in rule.keywords)
        优先级：priority 数值越大越优先，取最高优先级匹配。
        """
        matched: Optional[tuple[str, str]] = None
        best_priority = -1

        for rule in self._rules:
            if all(kw in normalized for kw in rule.keywords):
                if rule.priority >= best_priority:
                    best_priority = rule.priority
                    matched = (rule.sql, rule.explanation)

        return matched

    @property
    def rules(self) -> list[Rule]:
        """返回所有规则（用于调试/测试）"""
        return self._rules
