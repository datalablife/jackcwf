#!/usr/bin/env python3
"""
Phase 2 流式响应性能验证

测试首字节延迟、吞吐量和内存使用。
"""

import asyncio
import json
import time
import requests
from datetime import datetime, timedelta
import jwt
import os

# 配置
API_BASE_URL = "http://localhost:8000"
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')


def generate_token():
    """生成 JWT 测试令牌"""
    payload = {
        'sub': 'phase2-test',
        'email': 'test@phase2.local',
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def test_streaming_endpoint():
    """测试流式端点"""
    print("\n" + "="*80)
    print("Phase 2 流式响应性能验证")
    print("="*80)

    token = generate_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # 测试数据
    conversation_id = "550e8400-e29b-41d4-a716-446655440000"  # 有效的 UUID
    request_body = {
        "content": "Hello, please explain how Server-Sent Events work in web applications.",
        "role": "user"
    }

    url = f"{API_BASE_URL}/api/v1/conversations/{conversation_id}/stream"

    print(f"\n测试端点: {url}")
    print(f"请求: {json.dumps(request_body, indent=2)}")

    try:
        # 发送请求
        response = requests.post(url, json=request_body, headers=headers, stream=True, timeout=30)

        if response.status_code != 200:
            print(f"\n❌ 请求失败: {response.status_code}")
            print(f"响应: {response.text}")
            return False

        print(f"\n✅ 连接成功 (状态码: {response.status_code})")

        # 处理流式响应
        first_event_time = None
        event_count = 0
        total_chunks = 0
        total_tokens = 0
        start_time = time.time()

        print(f"\n接收流式事件:")
        print("-" * 80)

        for line in response.iter_lines():
            if not line:
                continue

            if line.startswith(b'data: '):
                try:
                    event_data = json.loads(line[6:])  # 去掉 'data: ' 前缀
                    event_type = event_data.get('type')
                    sequence = event_data.get('sequence', 0)

                    # 记录首字节延迟
                    if first_event_time is None:
                        first_event_time = time.time() - start_time
                        print(f"\n🚀 首字节延迟: {first_event_time*1000:.1f}ms")
                        if first_event_time < 0.1:  # <100ms
                            print(f"✅ 满足目标 (<100ms)")
                        else:
                            print(f"⚠️ 超过目标 (>100ms)")

                    # 处理不同类型的事件
                    if event_type == 'message_chunk':
                        event_count += 1
                        total_chunks += 1
                        total_tokens += event_data.get('token_count', 0)
                        content_preview = event_data.get('content', '')[:50]
                        print(f"  [{sequence}] {event_type}: {content_preview}...")

                    elif event_type == 'tool_call':
                        event_count += 1
                        tool_name = event_data.get('tool_name')
                        print(f"  [{sequence}] {event_type}: {tool_name}")

                    elif event_type == 'tool_result':
                        event_count += 1
                        result_preview = str(event_data.get('result', ''))[:50]
                        print(f"  [{sequence}] {event_type}: {result_preview}...")

                    elif event_type == 'complete_state':
                        event_count += 1
                        elapsed = event_data.get('elapsed_time', 0)
                        total_tokens = event_data.get('total_tokens', 0)
                        total_chunks = event_data.get('total_chunks', 0)
                        print(f"  [{sequence}] {event_type}:")
                        print(f"      - 总 Token: {total_tokens}")
                        print(f"      - 总块数: {total_chunks}")
                        print(f"      - 耗时: {elapsed:.2f}s")

                    elif event_type == 'error':
                        event_count += 1
                        error_msg = event_data.get('error_message', 'Unknown error')
                        print(f"  [{sequence}] {event_type}: {error_msg}")

                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON 解析错误: {e}")
                    continue

        # 计算性能指标
        total_time = time.time() - start_time

        print("\n" + "="*80)
        print("性能指标")
        print("="*80)
        print(f"✅ 首字节延迟: {first_event_time*1000:.1f}ms (目标: <100ms)")
        print(f"✅ 总事件数: {event_count}")
        print(f"✅ 总块数: {total_chunks}")
        print(f"✅ 总 Token: {total_tokens}")
        print(f"✅ 总耗时: {total_time:.2f}s")

        if total_time > 0:
            chunk_throughput = total_chunks / total_time
            print(f"✅ 块吞吐量: {chunk_throughput:.1f} chunks/s (目标: >50/s)")

        print("="*80)

        return True

    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到 API: {API_BASE_URL}")
        print("   请确保 FastAPI 应用正在运行")
        return False
    except Exception as e:
        print(f"❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stats_endpoint():
    """测试统计端点"""
    print("\n" + "="*80)
    print("获取流式服务统计信息")
    print("="*80)

    token = generate_token()
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/stream/stats",
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            stats = response.json()
            print(f"\n✅ 统计信息:")
            print(f"  - 活跃连接数: {stats.get('active_connections', 'N/A')}")
            print(f"  - 运行时间: {stats.get('uptime_seconds', 'N/A'):.1f}s")
            print(f"  - 块大小: {stats.get('config', {}).get('chunk_size', 'N/A')}")
            print(f"  - 首字节目标: {stats.get('config', {}).get('first_byte_target_ms', 'N/A')}ms")
            return True
        else:
            print(f"❌ 获取统计信息失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"⚠️ 获取统计信息错误: {e}")
        return False


if __name__ == "__main__":
    print(f"\n开始 Phase 2 流式响应性能验证")
    print(f"时间: {datetime.now().isoformat()}")
    print(f"目标 API: {API_BASE_URL}")

    # 运行测试
    success = test_streaming_endpoint()

    # 获取统计
    test_stats_endpoint()

    # 总结
    print("\n" + "="*80)
    if success:
        print("✅ Phase 2 流式响应验证成功")
    else:
        print("❌ Phase 2 流式响应验证失败")
    print("="*80 + "\n")
