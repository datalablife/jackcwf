#!/usr/bin/env python3
"""
健康监控脚本 - 定期检查前后端服务
支持 Supervisor 的自动重启机制
"""

import asyncio
import logging
import httpx
import os
import psutil
import signal
from datetime import datetime
from typing import Dict, Tuple
from pathlib import Path

# ============================================
# 配置
# ============================================

# 监控配置
BACKEND_URL = os.getenv("BACKEND_HEALTH_URL", "http://localhost:8000/health")
FRONTEND_URL = os.getenv("FRONTEND_HEALTH_URL", "http://localhost:3000")
CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))  # 秒
MAX_FAILURES = int(os.getenv("MAX_HEALTH_FAILURES", "3"))
TIMEOUT = int(os.getenv("HEALTH_CHECK_TIMEOUT", "5"))  # 秒

# 告警配置
ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "")
ENABLE_ALERTS = bool(ALERT_WEBHOOK_URL)

# 日志配置
LOG_DIR = Path("/var/log/app")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ============================================
# 日志设置
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到 stdout (Supervisor 日志)
        logging.FileHandler(LOG_DIR / "health_monitor.log"),  # 输出到文件
    ]
)

logger = logging.getLogger(__name__)

# ============================================
# 健康检查类
# ============================================

class HealthMonitor:
    def __init__(self):
        self.backend_failures = 0
        self.frontend_failures = 0
        self.running = True
        self.last_alert_time: Dict[str, float] = {}

    async def check_backend(self) -> bool:
        """检查后端健康状态"""
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.get(BACKEND_URL)
                if response.status_code == 200:
                    self.backend_failures = 0
                    logger.debug(f"✓ Backend health check passed: {BACKEND_URL}")
                    return True
                else:
                    self.backend_failures += 1
                    logger.warning(f"✗ Backend health check failed (HTTP {response.status_code})")
                    return False
        except Exception as e:
            self.backend_failures += 1
            logger.warning(f"✗ Backend health check failed: {str(e)}")
            return False

    async def check_frontend(self) -> bool:
        """检查前端可用性"""
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.get(FRONTEND_URL)
                if response.status_code == 200:
                    self.frontend_failures = 0
                    logger.debug(f"✓ Frontend health check passed: {FRONTEND_URL}")
                    return True
                else:
                    self.frontend_failures += 1
                    logger.warning(f"✗ Frontend health check failed (HTTP {response.status_code})")
                    return False
        except Exception as e:
            self.frontend_failures += 1
            logger.warning(f"✗ Frontend health check failed: {str(e)}")
            return False

    def get_system_metrics(self) -> Dict:
        """获取系统资源使用情况"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}

    async def send_alert(self, message: str, severity: str = "warning"):
        """发送告警通知 (Webhook)"""
        if not ENABLE_ALERTS:
            return

        # 防止告警轰炸 (相同告警 5 分钟内只发送一次)
        alert_key = f"{severity}:{message[:50]}"
        now = datetime.now().timestamp()
        last_time = self.last_alert_time.get(alert_key, 0)

        if now - last_time < 300:  # 5 分钟
            return

        self.last_alert_time[alert_key] = now

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                payload = {
                    "text": f"[{severity.upper()}] {message}",
                    "timestamp": datetime.now().isoformat(),
                    "service": "health-monitor",
                }
                await client.post(ALERT_WEBHOOK_URL, json=payload)
                logger.info(f"Alert sent: {message}")
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    async def handle_failure(self, service: str):
        """处理服务故障"""
        if service == "backend":
            failures = self.backend_failures
        else:
            failures = self.frontend_failures

        # 记录失败情况
        logger.error(f"{service} health check failed ({failures}/{MAX_FAILURES})")

        # 达到最大失败次数，Supervisor 将自动重启
        if failures >= MAX_FAILURES:
            message = f"{service.upper()} service failed {MAX_FAILURES} health checks, triggering restart"
            logger.error(message)
            await self.send_alert(message, severity="critical")

    async def run(self):
        """主监控循环"""
        logger.info("Health monitor started")
        logger.info(f"Backend URL: {BACKEND_URL}")
        logger.info(f"Frontend URL: {FRONTEND_URL}")
        logger.info(f"Check interval: {CHECK_INTERVAL}s")
        logger.info(f"Max failures: {MAX_FAILURES}")

        # 等待初始启动
        logger.info("Waiting 30s for services to start...")
        await asyncio.sleep(30)

        while self.running:
            try:
                # 执行健康检查
                backend_ok = await self.check_backend()
                frontend_ok = await self.check_frontend()

                # 处理失败
                if not backend_ok:
                    await self.handle_failure("backend")
                if not frontend_ok:
                    await self.handle_failure("frontend")

                # 记录系统指标
                metrics = self.get_system_metrics()
                if metrics:
                    logger.info(
                        f"System metrics - CPU: {metrics['cpu_percent']:.1f}%, "
                        f"Memory: {metrics['memory_percent']:.1f}%, "
                        f"Disk: {metrics['disk_percent']:.1f}%"
                    )

                    # 高资源使用告警
                    if metrics["cpu_percent"] > 80:
                        await self.send_alert(f"High CPU: {metrics['cpu_percent']:.1f}%", "warning")
                    if metrics["memory_percent"] > 85:
                        await self.send_alert(f"High Memory: {metrics['memory_percent']:.1f}%", "warning")

                # 等待下一次检查
                await asyncio.sleep(CHECK_INTERVAL)

            except Exception as e:
                logger.error(f"Unexpected error in health monitor: {e}")
                await asyncio.sleep(CHECK_INTERVAL)

    def stop(self):
        """停止监控"""
        self.running = False
        logger.info("Health monitor stopped")

# ============================================
# 信号处理
# ============================================

monitor = HealthMonitor()

def signal_handler(signum, frame):
    """处理 SIGTERM 和 SIGINT"""
    logger.info(f"Received signal {signum}, shutting down...")
    monitor.stop()

# ============================================
# 主函数
# ============================================

async def main():
    """启动健康监控"""
    # 注册信号处理
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        await monitor.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        monitor.stop()

if __name__ == "__main__":
    asyncio.run(main())
