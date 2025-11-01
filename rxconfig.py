import os

import reflex as rx

# 检测是否在生产环境
reflex_env = os.getenv("REFLEX_ENV", "dev").lower()
is_production = reflex_env in ("prod", "production")

# 生产环境配置
# 在生产环境使用完整 URL，在开发/构建环境使用空字符串
api_url = "https://www.jackcwf.com" if is_production else ""

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
    ],
)
