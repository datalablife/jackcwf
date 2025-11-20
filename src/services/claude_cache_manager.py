"""
Claude Prompt Caching Manager

管理 Claude API Prompt Caching，实现系统提示、上下文等的缓存。
支持 ephemeral (5 分钟) 和 pin (无限期) 两种缓存模式。

性能目标：
- 缓存命中率: 60-80%
- 成本节省: 90% (缓存读取 $0.0003 vs 正常 $0.003)
- 年度节省: $19,440 (基于 1000 月度查询)
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import logging
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class CacheControlType(str, Enum):
    """缓存控制类型"""
    EPHEMERAL = "ephemeral"  # 临时缓存 (5 分钟)
    PIN = "pin"              # 固定缓存 (无限期)


@dataclass
class CostMetrics:
    """成本指标"""
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_cost: float = 0.0
    cache_read_cost: float = 0.0
    normal_cost: float = 0.0
    saved_cost: float = 0.0
    savings_percent: float = 0.0

    # 价格常数 (Claude 3.5 Sonnet)
    CACHE_WRITE_PRICE = 0.0015  # $0.0015 per 1K tokens
    CACHE_READ_PRICE = 0.0003   # $0.0003 per 1K tokens
    NORMAL_PRICE = 0.003        # $0.003 per 1K tokens


@dataclass
class PromptCacheEntry:
    """缓存条目"""
    cache_key: str
    content: str
    token_count: int
    cache_control_type: CacheControlType = CacheControlType.EPHEMERAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: datetime = field(default_factory=datetime.utcnow)
    hit_count: int = 0
    total_saved_cost: float = 0.0

    def get_content_hash(self) -> str:
        """获取内容哈希，用于检测缓存失效"""
        return hashlib.md5(self.content.encode()).hexdigest()

    def is_expired(self, ttl_minutes: int = 5) -> bool:
        """检查缓存是否过期 (仅对 ephemeral 有效)"""
        if self.cache_control_type == CacheControlType.PIN:
            return False  # PIN 缓存不过期
        return datetime.utcnow() > self.last_used_at + timedelta(minutes=ttl_minutes)

    def to_claude_format(self) -> Dict[str, Any]:
        """转换为 Claude API 格式"""
        return {
            "type": "text",
            "text": self.content,
            "cache_control": {"type": self.cache_control_type.value}
        }


class ClaudePromptCacheManager:
    """
    Claude Prompt 缓存管理器

    管理三层缓存：
    1. 系统提示缓存 (pin) - 聊天、RAG、Agent 系统提示
    2. 上下文缓存 (ephemeral) - 对话历史、文档上下文、用户信息
    3. 查询缓存 (ephemeral) - 常见问题、相同查询
    """

    def __init__(self):
        # 三层缓存存储
        self._system_prompts_cache: Dict[str, PromptCacheEntry] = {}
        self._context_cache: Dict[str, PromptCacheEntry] = {}
        self._query_cache: Dict[str, PromptCacheEntry] = {}

        # 成本跟踪
        self.total_cache_write_tokens = 0
        self.total_cache_read_tokens = 0
        self.total_normal_tokens = 0
        self.cache_hit_count = 0
        self.cache_miss_count = 0

        # 启动时间
        self.start_time = datetime.utcnow()

    # ==================== 系统提示缓存 ====================

    def register_system_prompt(
        self,
        key: str,
        content: str,
        is_pinned: bool = True,
        token_count: Optional[int] = None,
    ) -> PromptCacheEntry:
        """
        注册系统提示缓存

        Args:
            key: 缓存键 (e.g., "chat_system", "rag_system")
            content: 系统提示内容
            is_pinned: 是否持久化缓存 (系统提示通常需要)
            token_count: Token 数 (如果为 None，则使用粗略估算)

        Returns:
            PromptCacheEntry
        """
        cache_control = CacheControlType.PIN if is_pinned else CacheControlType.EPHEMERAL

        if token_count is None:
            # 粗略估算：每个单词约 1.3 个 tokens
            token_count = max(1, int(len(content.split()) / 1.3))

        entry = PromptCacheEntry(
            cache_key=key,
            content=content,
            token_count=token_count,
            cache_control_type=cache_control,
        )

        self._system_prompts_cache[key] = entry
        logger.info(
            f"Registered system prompt cache: {key} "
            f"({entry.token_count} tokens, {cache_control.value})"
        )

        return entry

    def get_system_prompt_for_claude(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取 Claude API 格式的系统提示

        Returns:
            {
                "type": "text",
                "text": "...",
                "cache_control": {"type": "pin" | "ephemeral"}
            }
        """
        if key not in self._system_prompts_cache:
            logger.warning(f"System prompt cache not found: {key}")
            return None

        entry = self._system_prompts_cache[key]
        entry.last_used_at = datetime.utcnow()
        entry.hit_count += 1
        self.cache_hit_count += 1

        logger.debug(f"System prompt cache hit: {key} (hit #{entry.hit_count})")

        return entry.to_claude_format()

    # ==================== 上下文缓存 ====================

    def register_context(
        self,
        key: str,
        content: str,
        ttl_minutes: int = 1440,  # 默认 24 小时
        token_count: Optional[int] = None,
    ) -> PromptCacheEntry:
        """注册上下文缓存"""
        if token_count is None:
            token_count = max(1, int(len(content.split()) / 1.3))

        entry = PromptCacheEntry(
            cache_key=key,
            content=content,
            token_count=token_count,
            cache_control_type=CacheControlType.EPHEMERAL,
        )

        self._context_cache[key] = entry
        logger.info(f"Registered context cache: {key} ({entry.token_count} tokens)")

        return entry

    def get_context_for_claude(self, key: str) -> Optional[Dict[str, Any]]:
        """获取 Claude API 格式的上下文缓存"""
        if key not in self._context_cache:
            return None

        entry = self._context_cache[key]

        # 检查过期
        if entry.is_expired(ttl_minutes=24 * 60):
            logger.warning(f"Context cache expired: {key}")
            del self._context_cache[key]
            return None

        entry.last_used_at = datetime.utcnow()
        entry.hit_count += 1
        self.cache_hit_count += 1

        return entry.to_claude_format()

    # ==================== 成本跟踪 ====================

    def record_cache_hit(
        self,
        cache_read_tokens: int,
    ) -> CostMetrics:
        """
        记录缓存命中

        成本：
        - 缓存读取: $0.0003 / 1K tokens
        - 正常成本: $0.003 / 1K tokens
        - 节省: 90%
        """
        self.total_cache_read_tokens += cache_read_tokens
        self.cache_hit_count += 1

        # 成本计算
        cache_read_cost = (cache_read_tokens / 1000) * CostMetrics.CACHE_READ_PRICE
        normal_cost = (cache_read_tokens / 1000) * CostMetrics.NORMAL_PRICE
        saved_cost = normal_cost - cache_read_cost

        metrics = CostMetrics(
            cache_read_tokens=cache_read_tokens,
            cache_read_cost=cache_read_cost,
            normal_cost=normal_cost,
            saved_cost=saved_cost,
            savings_percent=90.0,
        )

        logger.info(
            f"Cache hit recorded: {cache_read_tokens} tokens, "
            f"saved ${saved_cost:.4f} (90% savings)"
        )

        return metrics

    def record_cache_write(
        self,
        cache_write_tokens: int,
    ) -> CostMetrics:
        """
        记录缓存写入

        成本：
        - 缓存写入: $0.0015 / 1K tokens (5x 正常成本)
        - 但后续读取时可以重用 (节省 90%)
        """
        self.total_cache_write_tokens += cache_write_tokens

        # 成本计算
        cache_write_cost = (cache_write_tokens / 1000) * CostMetrics.CACHE_WRITE_PRICE

        metrics = CostMetrics(
            cache_write_tokens=cache_write_tokens,
            cache_write_cost=cache_write_cost,
        )

        logger.info(f"Cache write recorded: {cache_write_tokens} tokens, cost ${cache_write_cost:.4f}")

        return metrics

    def record_cache_miss(
        self,
        input_tokens: int,
    ):
        """记录缓存未命中"""
        self.total_normal_tokens += input_tokens
        self.cache_miss_count += 1

        logger.debug(f"Cache miss recorded: {input_tokens} tokens")

    # ==================== 统计信息 ====================

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self.cache_hit_count + self.cache_miss_count
        hit_rate = (
            (self.cache_hit_count / total_requests * 100)
            if total_requests > 0
            else 0.0
        )

        # 成本计算
        cache_read_cost = (self.total_cache_read_tokens / 1000) * CostMetrics.CACHE_READ_PRICE
        normal_cost = (self.total_normal_tokens / 1000) * CostMetrics.NORMAL_PRICE
        cache_write_cost = (self.total_cache_write_tokens / 1000) * CostMetrics.CACHE_WRITE_PRICE

        total_actual_cost = cache_read_cost + cache_write_cost + normal_cost
        total_cost_without_cache = (
            (self.total_cache_read_tokens + self.total_normal_tokens) / 1000 * CostMetrics.NORMAL_PRICE
        )
        total_saved_cost = total_cost_without_cache - total_actual_cost

        return {
            # 缓存统计
            "system_prompts_cached": len(self._system_prompts_cache),
            "contexts_cached": len(self._context_cache),
            "queries_cached": len(self._query_cache),

            # Token 统计
            "total_cache_write_tokens": self.total_cache_write_tokens,
            "total_cache_read_tokens": self.total_cache_read_tokens,
            "total_normal_tokens": self.total_normal_tokens,
            "total_tokens": self.total_cache_write_tokens + self.total_cache_read_tokens + self.total_normal_tokens,

            # 命中率
            "cache_hit_count": self.cache_hit_count,
            "cache_miss_count": self.cache_miss_count,
            "hit_rate_percent": round(hit_rate, 2),

            # 成本统计
            "cache_read_cost": round(cache_read_cost, 4),
            "cache_write_cost": round(cache_write_cost, 4),
            "normal_cost": round(normal_cost, 4),
            "total_actual_cost": round(total_actual_cost, 4),
            "total_cost_without_cache": round(total_cost_without_cache, 4),
            "total_saved_cost": round(total_saved_cost, 4),
            "savings_percent": round(
                (total_saved_cost / total_cost_without_cache * 100) if total_cost_without_cache > 0 else 0,
                2
            ),

            # 运行时间
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
        }

    def estimate_monthly_savings(self, monthly_queries: int = 1000, hit_rate: float = 0.6) -> Dict[str, float]:
        """
        估算月度节省

        Args:
            monthly_queries: 每月查询数
            hit_rate: 缓存命中率

        Returns:
            月度成本估算
        """
        monthly_hits = monthly_queries * hit_rate
        monthly_misses = monthly_queries * (1 - hit_rate)

        # 平均 tokens/query (包括系统提示和上下文)
        avg_tokens_per_query = 6050

        # 成本计算
        hit_cost = (monthly_hits * avg_tokens_per_query / 1000) * CostMetrics.CACHE_READ_PRICE
        miss_cost = (monthly_misses * avg_tokens_per_query / 1000) * CostMetrics.NORMAL_PRICE
        actual_monthly_cost = hit_cost + miss_cost

        without_cache_cost = (monthly_queries * avg_tokens_per_query / 1000) * CostMetrics.NORMAL_PRICE
        monthly_saved = without_cache_cost - actual_monthly_cost

        return {
            "monthly_queries": monthly_queries,
            "hit_rate_percent": hit_rate * 100,
            "monthly_hit_cost": round(hit_cost, 2),
            "monthly_miss_cost": round(miss_cost, 2),
            "actual_monthly_cost": round(actual_monthly_cost, 2),
            "cost_without_cache": round(without_cache_cost, 2),
            "monthly_saved": round(monthly_saved, 2),
            "annual_saved": round(monthly_saved * 12, 2),
        }

    def clear_cache(self, cache_type: Optional[str] = None):
        """清除缓存"""
        if cache_type is None or cache_type == "all":
            self._system_prompts_cache.clear()
            self._context_cache.clear()
            self._query_cache.clear()
            logger.info("Cleared all caches")
        elif cache_type == "system":
            self._system_prompts_cache.clear()
            logger.info("Cleared system prompt caches")
        elif cache_type == "context":
            self._context_cache.clear()
            logger.info("Cleared context caches")
        elif cache_type == "query":
            self._query_cache.clear()
            logger.info("Cleared query caches")


# 全局单例
_cache_manager: Optional[ClaudePromptCacheManager] = None


def get_claude_cache_manager() -> ClaudePromptCacheManager:
    """获取或创建全局缓存管理器"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = ClaudePromptCacheManager()
        logger.info("Initialized Claude Prompt Cache Manager")
    return _cache_manager


def reset_claude_cache_manager():
    """重置全局缓存管理器 (用于测试)"""
    global _cache_manager
    _cache_manager = None
