"""
Analytics API Routes

Provides endpoints for tracking and analyzing frontend performance metrics
and user analytics data.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


class PerformanceMetric(BaseModel):
    """Frontend performance metric (Web Vitals)"""

    name: str = Field(..., description="Metric name (LCP, FID, CLS, etc.)")
    value: float = Field(..., description="Metric value in milliseconds or score")
    rating: Literal["good", "needs-improvement", "poor"] = Field(
        ..., description="Performance rating"
    )
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
    url: str = Field(..., description="Page URL where metric was measured")
    user_agent: Optional[str] = Field(None, description="User agent string")


class ResourceTiming(BaseModel):
    """Resource timing data"""

    name: str = Field(..., description="Resource URL")
    duration: float = Field(..., description="Load duration in milliseconds")
    type: str = Field(..., description="Resource type (script, stylesheet, etc.)")


class PerformanceStats(BaseModel):
    """Performance statistics summary"""

    metric_name: str
    count: int
    avg_value: float
    p50: float
    p95: float
    p99: float
    good_count: int
    needs_improvement_count: int
    poor_count: int


@router.post("/performance", status_code=201)
async def record_performance_metric(metric: PerformanceMetric):
    """
    Record frontend performance metric for analysis.

    Stores Core Web Vitals and other performance metrics for monitoring and analysis.

    **Metrics:**
    - LCP (Largest Contentful Paint): Target <2.5s
    - FID (First Input Delay): Target <100ms
    - CLS (Cumulative Layout Shift): Target <0.1
    - FCP (First Contentful Paint): Target <1.8s
    - TTFB (Time to First Byte): Target <800ms

    **Example:**
    ```json
    {
      "name": "LCP",
      "value": 2150,
      "rating": "good",
      "timestamp": 1700000000000,
      "url": "https://pgvctor.jackcwf.com/",
      "user_agent": "Mozilla/5.0 ..."
    }
    ```
    """
    try:
        # Log the metric
        logger.info(
            f"Performance Metric: {metric.name}={metric.value:.2f}ms "
            f"(rating={metric.rating}, url={metric.url})"
        )

        # TODO: Store in database for analytics dashboard
        # await performance_repository.create(metric)

        # TODO: Update Prometheus metrics
        # from src.infrastructure.monitoring import frontend_performance_histogram
        # frontend_performance_histogram.labels(
        #     metric_name=metric.name,
        #     rating=metric.rating
        # ).observe(metric.value / 1000)

        # TODO: Check if metric violates thresholds and alert
        # if metric.rating == "poor":
        #     await send_alert(f"Poor {metric.name} detected: {metric.value}ms")

        return {
            "status": "recorded",
            "metric": metric.name,
            "value": metric.value,
            "rating": metric.rating,
        }

    except Exception as e:
        logger.error(f"Failed to record performance metric: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to record performance metric"
        )


@router.post("/resource-timing", status_code=201)
async def record_resource_timing(timings: list[ResourceTiming]):
    """
    Record resource timing data for slow resource analysis.

    Helps identify slow-loading assets and optimize bundle sizes.

    **Example:**
    ```json
    [
      {
        "name": "https://cdn.example.com/app.js",
        "duration": 1250,
        "type": "script"
      }
    ]
    ```
    """
    try:
        slow_resources = [t for t in timings if t.duration > 1000]

        if slow_resources:
            logger.warning(
                f"Slow resources detected: {len(slow_resources)} resources took >1s"
            )
            for resource in slow_resources:
                logger.warning(
                    f"  - {resource.type}: {resource.name} ({resource.duration:.0f}ms)"
                )

        # TODO: Store in database
        # await resource_timing_repository.bulk_create(timings)

        return {
            "status": "recorded",
            "total_resources": len(timings),
            "slow_resources": len(slow_resources),
        }

    except Exception as e:
        logger.error(f"Failed to record resource timing: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to record resource timing"
        )


@router.get("/performance/stats", response_model=list[PerformanceStats])
async def get_performance_stats(
    metric_name: Optional[str] = None,
    hours: int = 24,
):
    """
    Get performance statistics for the specified time period.

    Returns aggregated statistics including percentiles and rating distribution.

    **Parameters:**
    - metric_name: Filter by metric name (LCP, FID, CLS, etc.)
    - hours: Time period in hours (default: 24)

    **Returns:**
    - List of PerformanceStats objects with aggregated metrics
    """
    try:
        # TODO: Query database for performance metrics
        # stats = await performance_repository.get_stats(
        #     metric_name=metric_name,
        #     since=datetime.now() - timedelta(hours=hours)
        # )

        # Placeholder response
        logger.info(f"Fetching performance stats for metric={metric_name}, hours={hours}")

        # Example response (replace with actual database query)
        example_stats = [
            {
                "metric_name": "LCP",
                "count": 1250,
                "avg_value": 2150.5,
                "p50": 2050.0,
                "p95": 3200.0,
                "p99": 4150.0,
                "good_count": 850,
                "needs_improvement_count": 300,
                "poor_count": 100,
            },
            {
                "metric_name": "FID",
                "count": 1180,
                "avg_value": 85.3,
                "p50": 75.0,
                "p95": 150.0,
                "p99": 250.0,
                "good_count": 1050,
                "needs_improvement_count": 100,
                "poor_count": 30,
            },
        ]

        if metric_name:
            return [s for s in example_stats if s["metric_name"] == metric_name]

        return example_stats

    except Exception as e:
        logger.error(f"Failed to fetch performance stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to fetch performance stats"
        )


@router.get("/performance/summary")
async def get_performance_summary():
    """
    Get overall performance health summary.

    Returns:
    - Overall performance grade
    - Core Web Vitals status
    - Top performance issues
    - Recent trends
    """
    try:
        # TODO: Calculate from database metrics
        # summary = await performance_repository.get_summary()

        # Placeholder response
        summary = {
            "overall_grade": "B+",
            "core_web_vitals": {
                "lcp": {"status": "good", "value": 2150, "target": 2500},
                "fid": {"status": "good", "value": 85, "target": 100},
                "cls": {"status": "needs-improvement", "value": 0.12, "target": 0.1},
            },
            "top_issues": [
                {
                    "type": "CLS",
                    "description": "Layout shifts detected in chat interface",
                    "impact": "medium",
                    "affected_users": 250,
                },
                {
                    "type": "Bundle Size",
                    "description": "Main bundle size exceeds 500KB",
                    "impact": "low",
                    "affected_users": 1200,
                },
            ],
            "trends": {
                "lcp_trend": "+5%",  # Worse
                "fid_trend": "-10%",  # Better
                "cls_trend": "+15%",  # Worse
            },
            "last_updated": datetime.utcnow().isoformat(),
        }

        return summary

    except Exception as e:
        logger.error(f"Failed to fetch performance summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to fetch performance summary"
        )


@router.delete("/performance/data")
async def clear_performance_data(days_to_keep: int = 30):
    """
    Clear old performance data to free up storage.

    Only keeps data from the last N days (default: 30).

    **Requires:** Admin authentication (TODO: add auth dependency)
    """
    try:
        # TODO: Delete old data from database
        # deleted_count = await performance_repository.delete_older_than(
        #     datetime.now() - timedelta(days=days_to_keep)
        # )

        logger.info(f"Cleared performance data older than {days_to_keep} days")

        return {
            "status": "cleared",
            "days_kept": days_to_keep,
            "deleted_count": 0,  # Placeholder
        }

    except Exception as e:
        logger.error(f"Failed to clear performance data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to clear performance data"
        )
