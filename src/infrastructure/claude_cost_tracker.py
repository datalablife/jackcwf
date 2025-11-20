"""
Claude API 成本追踪

追踪和分析 Claude API 的使用成本和节省额度。
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class CostRecord:
    """单次调用的成本记录"""
    timestamp: datetime
    query_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    model: str = "claude-3-5-sonnet-20241022"
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    cache_hit: bool = False

    @property
    def cache_read_cost(self) -> float:
        """缓存读取成本"""
        return (self.cache_read_tokens / 1000) * 0.0003

    @property
    def cache_write_cost(self) -> float:
        """缓存写入成本"""
        return (self.cache_write_tokens / 1000) * 0.0015

    @property
    def query_cost(self) -> float:
        """查询成本 (输出)"""
        return (self.query_tokens / 1000) * 0.003

    @property
    def total_cost(self) -> float:
        """总成本"""
        return self.cache_read_cost + self.cache_write_cost + self.query_cost

    @property
    def cost_without_cache(self) -> float:
        """如果没有缓存的成本"""
        input_tokens = (self.cache_read_tokens or self.cache_write_tokens or 0) + self.query_tokens
        return (input_tokens / 1000) * 0.003

    @property
    def saved_cost(self) -> float:
        """节省的成本"""
        if self.cache_hit:
            return self.cost_without_cache - self.total_cost
        return 0.0


class ClaudeApiCostTracker:
    """Claude API 成本追踪器"""

    def __init__(self):
        self.records: List[CostRecord] = []
        self.start_time = datetime.utcnow()

    def record_api_call(
        self,
        query_tokens: int,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        model: str = "claude-3-5-sonnet-20241022",
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        cache_hit: bool = False,
    ) -> CostRecord:
        """记录一次 API 调用"""
        record = CostRecord(
            timestamp=datetime.utcnow(),
            query_tokens=query_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            model=model,
            conversation_id=conversation_id,
            user_id=user_id,
            cache_hit=cache_hit,
        )
        self.records.append(record)
        return record

    def get_summary(self) -> Dict:
        """获取成本摘要"""
        if not self.records:
            return {
                "total_calls": 0,
                "total_cost": 0.0,
                "total_saved": 0.0,
                "savings_percent": 0.0,
            }

        total_calls = len(self.records)
        total_cost = sum(r.total_cost for r in self.records)
        cost_without_cache = sum(r.cost_without_cache for r in self.records)
        total_saved = cost_without_cache - total_cost

        cache_hits = sum(1 for r in self.records if r.cache_hit)
        cache_hit_rate = (cache_hits / total_calls * 100) if total_calls > 0 else 0

        return {
            "total_calls": total_calls,
            "cache_hits": cache_hits,
            "cache_misses": total_calls - cache_hits,
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "total_tokens": sum(r.query_tokens + r.cache_read_tokens + r.cache_write_tokens for r in self.records),
            "total_cost": round(total_cost, 4),
            "cost_without_cache": round(cost_without_cache, 4),
            "total_saved": round(total_saved, 4),
            "savings_percent": round((total_saved / cost_without_cache * 100) if cost_without_cache > 0 else 0, 2),
        }

    def get_daily_summary(self, days_back: int = 1) -> Dict:
        """获取指定天数的日均成本"""
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        recent_records = [r for r in self.records if r.timestamp >= cutoff]

        if not recent_records:
            return {}

        summary = {
            "period_days": days_back,
            "total_calls": len(recent_records),
            "daily_avg_calls": len(recent_records) / max(1, days_back),
        }

        total_cost = sum(r.total_cost for r in recent_records)
        cost_without_cache = sum(r.cost_without_cache for r in recent_records)
        total_saved = cost_without_cache - total_cost

        summary.update({
            "total_cost": round(total_cost, 4),
            "daily_avg_cost": round(total_cost / max(1, days_back), 4),
            "total_saved": round(total_saved, 4),
            "daily_avg_saved": round(total_saved / max(1, days_back), 4),
            "monthly_projection_cost": round(total_cost / days_back * 30, 2),
            "monthly_projection_saved": round(total_saved / days_back * 30, 2),
        })

        return summary

    def get_user_summary(self, user_id: str) -> Dict:
        """获取特定用户的成本摘要"""
        user_records = [r for r in self.records if r.user_id == user_id]

        if not user_records:
            return {
                "user_id": user_id,
                "total_calls": 0,
                "total_cost": 0.0,
            }

        total_cost = sum(r.total_cost for r in user_records)
        cost_without_cache = sum(r.cost_without_cache for r in user_records)
        total_saved = cost_without_cache - total_cost

        return {
            "user_id": user_id,
            "total_calls": len(user_records),
            "total_cost": round(total_cost, 4),
            "total_saved": round(total_saved, 4),
            "avg_cost_per_call": round(total_cost / len(user_records), 4) if user_records else 0.0,
        }

    def estimate_monthly_cost(self, avg_calls_per_day: int = 33, cache_hit_rate: float = 0.6) -> Dict:
        """
        估算月度成本

        假设：
        - 平均每天 33 个调用 (1000/月)
        - 缓存命中率 60%
        """
        monthly_calls = avg_calls_per_day * 30
        monthly_hits = monthly_calls * cache_hit_rate
        monthly_misses = monthly_calls * (1 - cache_hit_rate)

        # 平均 tokens
        avg_input_tokens = 6000
        avg_output_tokens = 500

        hit_cost = (monthly_hits * avg_input_tokens / 1000) * 0.0003  # 缓存读取
        miss_cost = (monthly_misses * (avg_input_tokens + avg_output_tokens) / 1000) * 0.003
        output_cost = (monthly_calls * avg_output_tokens / 1000) * 0.003

        actual_monthly_cost = hit_cost + miss_cost + output_cost

        without_cache_input = monthly_calls * avg_input_tokens
        without_cache_output = monthly_calls * avg_output_tokens
        cost_without_cache = (
            (without_cache_input / 1000) * 0.003 +  # 输入
            (without_cache_output / 1000) * 0.003     # 输出
        )

        monthly_saved = cost_without_cache - actual_monthly_cost

        return {
            "monthly_calls": monthly_calls,
            "cache_hit_rate_percent": cache_hit_rate * 100,
            "hit_cost": round(hit_cost, 2),
            "miss_cost": round(miss_cost, 2),
            "output_cost": round(output_cost, 2),
            "actual_monthly_cost": round(actual_monthly_cost, 2),
            "cost_without_cache": round(cost_without_cache, 2),
            "monthly_saved": round(monthly_saved, 2),
            "annual_saved": round(monthly_saved * 12, 2),
            "savings_percent": round((monthly_saved / cost_without_cache * 100) if cost_without_cache > 0 else 0, 2),
        }


# 全局单例
_cost_tracker: Optional[ClaudeApiCostTracker] = None


def get_cost_tracker() -> ClaudeApiCostTracker:
    """获取或创建全局成本追踪器"""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = ClaudeApiCostTracker()
        logger.info("Initialized Claude API Cost Tracker")
    return _cost_tracker
