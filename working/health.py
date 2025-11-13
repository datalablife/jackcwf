"""Health check endpoint for container monitoring and Coolify integration."""

import os
from datetime import datetime
from typing import Dict, Any

import reflex as rx


class HealthCheckState(rx.State):
    """Health check state for monitoring application status."""

    @staticmethod
    def get_health_status() -> Dict[str, Any]:
        """
        Get comprehensive health status of the application.

        Returns:
            Dictionary containing health status information
        """
        status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "working",
            "environment": os.getenv("REFLEX_ENV", "dev"),
        }

        # Add database status if DATABASE_URL is configured
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            try:
                from sqlalchemy import create_engine

                # Quick connection test
                engine = create_engine(database_url, pool_pre_ping=True)
                with engine.connect() as conn:
                    conn.execute("SELECT 1")

                status["database"] = "connected"
            except Exception as e:
                status["database"] = "disconnected"
                status["database_error"] = str(e)
                status["status"] = "degraded"
        else:
            status["database"] = "not_configured"

        # Add version information if available
        try:
            with open("/app/.git/HEAD", "r") as f:
                git_ref = f.read().strip()
                if git_ref.startswith("ref:"):
                    ref_path = git_ref.split(": ")[1]
                    with open(f"/app/.git/{ref_path}", "r") as ref_file:
                        status["git_commit"] = ref_file.read().strip()[:8]
        except:
            pass

        return status


@rx.page(route="/health", title="Health Check")
def health_page() -> rx.Component:
    """
    Health check page for monitoring.

    This endpoint is used by:
    - Docker HEALTHCHECK
    - Coolify monitoring
    - Load balancers
    - Uptime monitoring services
    """
    health_status = HealthCheckState.get_health_status()

    return rx.container(
        rx.vstack(
            rx.heading("Health Check", size="8"),
            rx.divider(),
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.text("Status:", weight="bold"),
                        rx.badge(
                            health_status.get("status", "unknown"),
                            color_scheme=(
                                "green"
                                if health_status.get("status") == "healthy"
                                else "orange"
                            ),
                        ),
                    ),
                    rx.hstack(
                        rx.text("Service:", weight="bold"),
                        rx.text(health_status.get("service", "N/A")),
                    ),
                    rx.hstack(
                        rx.text("Environment:", weight="bold"),
                        rx.text(health_status.get("environment", "N/A")),
                    ),
                    rx.hstack(
                        rx.text("Database:", weight="bold"),
                        rx.badge(
                            health_status.get("database", "unknown"),
                            color_scheme=(
                                "green"
                                if health_status.get("database") == "connected"
                                else "gray"
                            ),
                        ),
                    ),
                    rx.hstack(
                        rx.text("Timestamp:", weight="bold"),
                        rx.text(health_status.get("timestamp", "N/A")),
                    ),
                    rx.cond(
                        health_status.get("git_commit") is not None,
                        rx.hstack(
                            rx.text("Version:", weight="bold"),
                            rx.text(health_status.get("git_commit", "N/A")),
                        ),
                    ),
                    spacing="4",
                ),
            ),
            spacing="4",
            padding="4",
        ),
        max_width="600px",
    )
