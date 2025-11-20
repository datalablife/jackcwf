"""
Claude Prompt 缓存管理 API 端点

提供缓存统计、成本分析和缓存管理的 REST API 端点。
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging

from src.middleware.auth_middleware import get_current_user
from src.services.claude_cache_manager import get_claude_cache_manager
from src.infrastructure.claude_cost_tracker import get_cost_tracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Claude Cache Management"])


@router.get("/claude-cache/stats")
async def get_cache_stats(user_id: str = Depends(get_current_user)):
    """
    获取 Claude Prompt 缓存统计信息

    Returns:
        缓存统计数据，包含：
        - 缓存条目数 (系统提示、上下文、查询)
        - Token 统计 (写入、读取、正常)
        - 命中率和命中数
        - 成本统计和节省额度
        - 运行时间
    """
    try:
        cache_manager = get_claude_cache_manager()
        stats = cache_manager.get_cache_stats()

        return {
            "success": True,
            "data": stats,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get cache statistics")


@router.get("/claude-cache/cost-analysis")
async def get_cost_analysis(
    days_back: int = 1,
    user_id: Optional[str] = None,
    user_id_auth: str = Depends(get_current_user),
):
    """
    获取 Claude API 成本分析

    Query Parameters:
        days_back: 查询天数 (默认: 1)
        user_id: 查询特定用户的成本 (可选)

    Returns:
        成本分析数据，包含：
        - 调用统计
        - 成本统计
        - 缓存命中率
        - 节省额度
        - 月度预测
    """
    try:
        cost_tracker = get_cost_tracker()

        if user_id:
            # 获取特定用户的成本统计
            user_summary = cost_tracker.get_user_summary(user_id)
            return {
                "success": True,
                "data": user_summary,
                "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            }
        else:
            # 获取总体成本统计
            summary = cost_tracker.get_summary()
            daily_summary = cost_tracker.get_daily_summary(days_back=days_back)
            estimate = cost_tracker.estimate_monthly_cost()

            return {
                "success": True,
                "data": {
                    "overall": summary,
                    "daily": daily_summary,
                    "estimate": estimate,
                },
                "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            }
    except Exception as e:
        logger.error(f"Error getting cost analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get cost analysis")


@router.get("/claude-cache/monthly-projection")
async def get_monthly_projection(
    avg_calls_per_day: int = 33,
    cache_hit_rate: float = 0.6,
    user_id: str = Depends(get_current_user),
):
    """
    获取月度成本预测

    Query Parameters:
        avg_calls_per_day: 每天平均调用数 (默认: 33)
        cache_hit_rate: 缓存命中率 (默认: 0.6 = 60%)

    Returns:
        月度成本预测数据
    """
    try:
        cost_tracker = get_cost_tracker()
        projection = cost_tracker.estimate_monthly_cost(
            avg_calls_per_day=avg_calls_per_day,
            cache_hit_rate=cache_hit_rate,
        )

        return {
            "success": True,
            "data": projection,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting monthly projection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get monthly projection")


@router.post("/claude-cache/clear")
async def clear_cache(
    cache_type: Optional[str] = None,
    user_id: str = Depends(get_current_user),
):
    """
    清除 Claude Prompt 缓存

    Query Parameters:
        cache_type: 缓存类型 ("all", "system", "context", "query") (默认: "all")

    Returns:
        清除结果
    """
    try:
        cache_manager = get_claude_cache_manager()
        cache_manager.clear_cache(cache_type=cache_type)

        return {
            "success": True,
            "message": f"Cleared {'all caches' if cache_type is None or cache_type == 'all' else cache_type + ' cache'}",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.get("/claude-cache/health")
async def get_cache_health(user_id: str = Depends(get_current_user)):
    """
    获取缓存健康状态

    Returns:
        缓存系统的健康检查信息
    """
    try:
        cache_manager = get_claude_cache_manager()
        cost_tracker = get_cost_tracker()

        stats = cache_manager.get_cache_stats()
        cost_summary = cost_tracker.get_summary()

        # 健康检查逻辑
        is_healthy = True
        warnings = []

        # 检查命中率
        if stats.get("hit_rate_percent", 0) < 10:
            warnings.append("Low cache hit rate (< 10%)")

        # 检查缓存大小（如果缓存过多可能有问题）
        total_cached = (
            stats.get("system_prompts_cached", 0) +
            stats.get("contexts_cached", 0) +
            stats.get("queries_cached", 0)
        )
        if total_cached > 1000:
            warnings.append("Large number of cached items (> 1000)")
            is_healthy = False

        return {
            "success": True,
            "data": {
                "is_healthy": is_healthy,
                "warnings": warnings,
                "stats": stats,
                "cost_summary": cost_summary,
            },
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting cache health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get cache health status")
