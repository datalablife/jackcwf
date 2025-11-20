#!/usr/bin/env python3
"""
Phase 3 Claude Prompt 缓存验证测试

测试缓存功能、成本计算和 API 端点。
"""

import asyncio
import sys
from datetime import datetime

# 导入模块
from src.services.claude_cache_manager import (
    get_claude_cache_manager,
    CacheControlType,
    PromptCacheEntry,
)
from src.infrastructure.claude_cost_tracker import get_cost_tracker
from src.services.claude_integration import ClaudeAgentIntegration


def test_cache_manager():
    """测试缓存管理器"""
    print("\n" + "="*80)
    print("TEST 1: Claude Prompt Cache Manager")
    print("="*80)

    cache_manager = get_claude_cache_manager()

    # 测试 1.1: 注册系统提示
    print("\n✓ Test 1.1: 注册系统提示")
    prompt = cache_manager.register_system_prompt(
        key="test_system",
        content="You are a helpful assistant." * 100,  # 大约 1000 tokens
        is_pinned=True,
    )
    print(f"  - 注册成功: key={prompt.cache_key}, tokens={prompt.token_count}")
    assert prompt.cache_key == "test_system"
    assert prompt.token_count > 0

    # 测试 1.2: 获取缓存的系统提示
    print("\n✓ Test 1.2: 获取缓存的系统提示")
    cached = cache_manager.get_system_prompt_for_claude("test_system")
    print(f"  - 缓存命中: {cached is not None}")
    print(f"  - 缓存控制: {cached.get('cache_control', {})}")
    assert cached is not None
    assert cached.get("type") == "text"

    # 测试 1.3: 注册上下文缓存
    print("\n✓ Test 1.3: 注册上下文缓存")
    context = cache_manager.register_context(
        key="test_context",
        content="Recent conversation: User asked about X, assistant replied with Y." * 50,
        ttl_minutes=1440,
    )
    print(f"  - 注册成功: key={context.cache_key}, tokens={context.token_count}")
    assert context.cache_key == "test_context"

    # 测试 1.4: 记录缓存命中
    print("\n✓ Test 1.4: 记录缓存命中")
    hit_metrics = cache_manager.record_cache_hit(cache_read_tokens=5000)
    print(f"  - 缓存读取: {hit_metrics.cache_read_tokens} tokens")
    print(f"  - 节省成本: ${hit_metrics.saved_cost:.4f}")
    assert hit_metrics.saved_cost > 0

    # 测试 1.5: 记录缓存写入
    print("\n✓ Test 1.5: 记录缓存写入")
    write_metrics = cache_manager.record_cache_write(cache_write_tokens=2000)
    print(f"  - 缓存写入: {write_metrics.cache_write_tokens} tokens")
    print(f"  - 写入成本: ${write_metrics.cache_write_cost:.4f}")
    assert write_metrics.cache_write_cost > 0

    # 测试 1.6: 获取统计信息
    print("\n✓ Test 1.6: 获取缓存统计信息")
    stats = cache_manager.get_cache_stats()
    print(f"  - 系统提示缓存: {stats['system_prompts_cached']} 个")
    print(f"  - 上下文缓存: {stats['contexts_cached']} 个")
    print(f"  - 缓存命中率: {stats['hit_rate_percent']:.1f}%")
    print(f"  - 已节省成本: ${stats['total_saved_cost']:.4f}")
    assert stats['hit_rate_percent'] >= 0

    # 测试 1.7: 月度节省估算
    print("\n✓ Test 1.7: 月度节省估算")
    savings = cache_manager.estimate_monthly_savings(
        monthly_queries=1000,
        hit_rate=0.6,
    )
    print(f"  - 月度节省: ${savings['monthly_saved']:.2f}")
    print(f"  - 年度节省: ${savings['annual_saved']:.2f}")
    assert savings['monthly_saved'] > 0

    print("\n✅ Test 1: Claude Prompt Cache Manager 通过")
    return True


def test_cost_tracker():
    """测试成本追踪器"""
    print("\n" + "="*80)
    print("TEST 2: Claude API Cost Tracker")
    print("="*80)

    cost_tracker = get_cost_tracker()

    # 测试 2.1: 记录 API 调用 (缓存命中)
    print("\n✓ Test 2.1: 记录缓存命中的 API 调用")
    record = cost_tracker.record_api_call(
        query_tokens=500,  # 输出 tokens
        cache_read_tokens=5000,  # 缓存读取
        user_id="test_user",
        cache_hit=True,
    )
    print(f"  - 查询 tokens: {record.query_tokens}")
    print(f"  - 缓存读取 tokens: {record.cache_read_tokens}")
    print(f"  - 总成本: ${record.total_cost:.4f}")
    print(f"  - 节省成本: ${record.saved_cost:.4f}")
    assert record.total_cost > 0
    assert record.saved_cost > 0

    # 测试 2.2: 记录 API 调用 (缓存未命中)
    print("\n✓ Test 2.2: 记录缓存未命中的 API 调用")
    record2 = cost_tracker.record_api_call(
        query_tokens=500,
        cache_write_tokens=6000,  # 缓存写入
        user_id="test_user",
        cache_hit=False,
    )
    print(f"  - 缓存写入 tokens: {record2.cache_write_tokens}")
    print(f"  - 总成本: ${record2.total_cost:.4f}")

    # 测试 2.3: 获取成本摘要
    print("\n✓ Test 2.3: 获取成本摘要")
    summary = cost_tracker.get_summary()
    print(f"  - 总调用数: {summary['total_calls']}")
    print(f"  - 缓存命中数: {summary['cache_hits']}")
    print(f"  - 缓存命中率: {summary['cache_hit_rate_percent']:.1f}%")
    print(f"  - 总成本: ${summary['total_cost']:.4f}")
    print(f"  - 已节省: ${summary['total_saved']:.4f}")
    assert summary['total_calls'] >= 2

    # 测试 2.4: 月度成本估算
    print("\n✓ Test 2.4: 月度成本估算")
    estimate = cost_tracker.estimate_monthly_cost(
        avg_calls_per_day=33,
        cache_hit_rate=0.6,
    )
    print(f"  - 月度调用数: {estimate['monthly_calls']}")
    print(f"  - 估算月度成本: ${estimate['actual_monthly_cost']:.2f}")
    print(f"  - 估算月度节省: ${estimate['monthly_saved']:.2f}")
    print(f"  - 估算年度节省: ${estimate['annual_saved']:.2f}")
    assert estimate['monthly_saved'] > 0

    # 测试 2.5: 用户成本摘要
    print("\n✓ Test 2.5: 用户成本摘要")
    user_summary = cost_tracker.get_user_summary("test_user")
    print(f"  - 用户: {user_summary['user_id']}")
    print(f"  - 调用数: {user_summary['total_calls']}")
    print(f"  - 总成本: ${user_summary['total_cost']:.4f}")
    assert user_summary['total_calls'] >= 2

    print("\n✅ Test 2: Claude API Cost Tracker 通过")
    return True


def test_claude_integration():
    """测试 Claude 集成"""
    print("\n" + "="*80)
    print("TEST 3: Claude Agent Integration")
    print("="*80)

    # 测试 3.1: 初始化集成
    print("\n✓ Test 3.1: 初始化 Claude 集成")
    ClaudeAgentIntegration.initialize_cache()
    print("  - 缓存管理器初始化完成")

    # 测试 3.2: 获取缓存的系统提示
    print("\n✓ Test 3.2: 获取缓存的系统提示")
    for prompt_type in ["chat", "rag", "agent"]:
        cached = ClaudeAgentIntegration.get_cached_system_prompt(prompt_type)
        print(f"  - {prompt_type} 系统提示缓存: {cached is not None}")
        assert cached is not None

    # 测试 3.3: 缓存对话上下文
    print("\n✓ Test 3.3: 缓存对话上下文")
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    context_block = ClaudeAgentIntegration.cache_conversation_context(
        conversation_id="test_conv",
        messages=messages,
    )
    print(f"  - 上下文缓存: {context_block is not None}")

    # 测试 3.4: 记录 API 使用
    print("\n✓ Test 3.4: 记录 API 使用和成本")
    cost_info = ClaudeAgentIntegration.record_api_usage(
        input_tokens=6000,
        output_tokens=500,
        cache_read_tokens=5000,
        conversation_id="test_conv",
        user_id="test_user",
        cache_hit=True,
    )
    print(f"  - 总成本: ${cost_info['total_cost']:.4f}")
    print(f"  - 节省成本: ${cost_info['saved_cost']:.4f}")
    print(f"  - 节省百分比: {cost_info['savings_percent']:.0f}%")

    # 测试 3.5: 构建带缓存的 Claude 请求
    print("\n✓ Test 3.5: 构建带缓存的 Claude 请求")
    request = ClaudeAgentIntegration.build_claude_request_with_cache(
        system_prompt_type="chat",
        messages=messages,
        conversation_id="test_conv",
    )
    print(f"  - 系统块数: {len(request['system'])}")
    print(f"  - 消息数: {len(request['messages'])}")
    assert len(request['system']) > 0

    # 测试 3.6: 获取缓存统计
    print("\n✓ Test 3.6: 获取缓存统计")
    stats = ClaudeAgentIntegration.get_cache_statistics()
    print(f"  - 系统提示缓存数: {stats['system_prompts_cached']}")
    print(f"  - 上下文缓存数: {stats['contexts_cached']}")

    # 测试 3.7: 获取成本摘要
    print("\n✓ Test 3.7: 获取成本摘要")
    cost_summary = ClaudeAgentIntegration.get_cost_summary()
    print(f"  - 总调用数: {cost_summary['total_calls']}")
    print(f"  - 命中率: {cost_summary.get('cache_hit_rate_percent', 0):.1f}%")
    print(f"  - 总节省: ${cost_summary['total_saved']:.4f}")

    print("\n✅ Test 3: Claude Agent Integration 通过")
    return True


def print_summary():
    """打印总结报告"""
    print("\n" + "="*80)
    print("Phase 3 成本节省总结")
    print("="*80)

    cache_manager = get_claude_cache_manager()
    cost_tracker = get_cost_tracker()

    # 缓存统计
    cache_stats = cache_manager.get_cache_stats()
    cost_summary = cost_tracker.get_summary()
    monthly_estimate = cost_tracker.estimate_monthly_cost()

    print(f"\n缓存统计:")
    print(f"  • 系统提示缓存: {cache_stats['system_prompts_cached']} 个")
    print(f"  • 上下文缓存: {cache_stats['contexts_cached']} 个")
    print(f"  • 总 Token 处理: {cache_stats['total_tokens']:,}")
    print(f"  • 缓存命中率: {cache_stats['hit_rate_percent']:.1f}%")

    print(f"\n成本统计:")
    print(f"  • 总调用数: {cost_summary['total_calls']}")
    print(f"  • 缓存命中数: {cost_summary['cache_hits']}")
    print(f"  • 实际总成本: ${cost_summary['total_cost']:.4f}")
    print(f"  • 未缓存成本: ${cost_summary['cost_without_cache']:.4f}")
    print(f"  • 已节省: ${cost_summary['total_saved']:.4f}")
    print(f"  • 节省百分比: {cost_summary['savings_percent']:.1f}%")

    print(f"\n月度预测 (1000 查询/月, 60% 命中率):")
    print(f"  • 月度调用数: {monthly_estimate['monthly_calls']:,}")
    print(f"  • 估算月度成本: ${monthly_estimate['actual_monthly_cost']:.2f}")
    print(f"  • 未缓存月度成本: ${monthly_estimate['cost_without_cache']:.2f}")
    print(f"  • 月度节省: ${monthly_estimate['monthly_saved']:.2f}")
    print(f"  • 年度节省: ${monthly_estimate['annual_saved']:.2f}")

    print("\n" + "="*80)


if __name__ == "__main__":
    print("\n🚀 Phase 3 Claude Prompt 缓存验证测试")
    print(f"时间: {datetime.now().isoformat()}")

    try:
        # 运行所有测试
        results = []
        results.append(("Cache Manager", test_cache_manager()))
        results.append(("Cost Tracker", test_cost_tracker()))
        results.append(("Claude Integration", test_claude_integration()))

        # 打印总结
        print_summary()

        # 最终结果
        print("\n" + "="*80)
        print("测试结果")
        print("="*80)
        all_passed = all(result[1] for result in results)

        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {test_name}")

        if all_passed:
            print("\n🎉 所有测试通过！Phase 3 已准备就绪")
            sys.exit(0)
        else:
            print("\n❌ 部分测试失败")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
