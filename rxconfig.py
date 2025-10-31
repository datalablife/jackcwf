import reflex as rx
import os

# 检测是否在生产环境
is_production = os.getenv("REFLEX_ENV", "dev") == "production"

# 生产环境配置
api_url = "https://www.jackcwf.com" if is_production else None

config = rx.Config(
    app_name="working",
    frontend_host="0.0.0.0",
    frontend_port=3000,
    backend_host="0.0.0.0",
    backend_port=8000,
    api_url=api_url,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)