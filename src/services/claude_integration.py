"""
Claude API 集成和缓存包装

为 AgentService 添加 Claude Prompt 缓存支持。
"""

from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from src.services.claude_cache_manager import (
    get_claude_cache_manager,
    CacheControlType,
)
from src.infrastructure.claude_cost_tracker import get_cost_tracker

logger = logging.getLogger(__name__)


class ClaudeAgentIntegration:
    """
    Claude Agent 集成

    为 Agent 添加 Prompt Caching 支持，包括：
    - 系统提示缓存
    - 上下文缓存
    - 成本追踪
    """

    # 系统提示缓存键定义
    CHAT_SYSTEM_PROMPT_KEY = "chat_system"
    RAG_SYSTEM_PROMPT_KEY = "rag_system"
    AGENT_SYSTEM_PROMPT_KEY = "agent_system"

    @staticmethod
    def initialize_cache():
        """初始化缓存管理器"""
        cache_manager = get_claude_cache_manager()

        # 注册常用系统提示
        chat_system_prompt = """You are a helpful AI assistant designed for having natural conversations.

Your responsibilities:
- Answer questions accurately and helpfully
- Engage in meaningful dialogue
- Clarify when you don't understand
- Be honest about your limitations"""

        cache_manager.register_system_prompt(
            key=ClaudeAgentIntegration.CHAT_SYSTEM_PROMPT_KEY,
            content=chat_system_prompt,
            is_pinned=True,
        )

        rag_system_prompt = """You are an AI assistant specialized in RAG (Retrieval-Augmented Generation).

Your responsibilities:
- Search and analyze documents
- Provide answers based on retrieved information
- Cite sources when using document information
- Synthesize information from multiple documents"""

        cache_manager.register_system_prompt(
            key=ClaudeAgentIntegration.RAG_SYSTEM_PROMPT_KEY,
            content=rag_system_prompt,
            is_pinned=True,
        )

        agent_system_prompt = """You are an AI agent with access to multiple tools.

Available capabilities:
- Search documents
- Query databases
- Perform web searches
- Execute tools

Always use the most appropriate tool for the task at hand."""

        cache_manager.register_system_prompt(
            key=ClaudeAgentIntegration.AGENT_SYSTEM_PROMPT_KEY,
            content=agent_system_prompt,
            is_pinned=True,
        )

        logger.info("Initialized Claude Agent with cached system prompts")

    @staticmethod
    def get_cached_system_prompt(prompt_type: str = "chat") -> Optional[Dict[str, Any]]:
        """
        获取缓存的系统提示

        Args:
            prompt_type: 提示类型 ("chat", "rag", "agent")

        Returns:
            Claude API 格式的系统提示块
        """
        cache_manager = get_claude_cache_manager()

        if prompt_type == "chat":
            return cache_manager.get_system_prompt_for_claude(
                ClaudeAgentIntegration.CHAT_SYSTEM_PROMPT_KEY
            )
        elif prompt_type == "rag":
            return cache_manager.get_system_prompt_for_claude(
                ClaudeAgentIntegration.RAG_SYSTEM_PROMPT_KEY
            )
        elif prompt_type == "agent":
            return cache_manager.get_system_prompt_for_claude(
                ClaudeAgentIntegration.AGENT_SYSTEM_PROMPT_KEY
            )
        else:
            logger.warning(f"Unknown prompt type: {prompt_type}")
            return None

    @staticmethod
    def cache_conversation_context(
        conversation_id: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 5000,
    ) -> Optional[Dict[str, Any]]:
        """
        缓存对话上下文

        Args:
            conversation_id: 对话 ID
            messages: 消息列表
            max_tokens: 最大 tokens

        Returns:
            Claude API 格式的上下文块
        """
        cache_manager = get_claude_cache_manager()

        # 构建上下文文本
        context_text = "Conversation history:\n\n"
        for msg in messages[-10:]:  # 仅保留最近 10 条消息
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            context_text += f"{role}: {content}\n"

        # 缓存上下文
        cache_key = f"context_{conversation_id}"
        cache_manager.register_context(
            key=cache_key,
            content=context_text,
            ttl_minutes=1440,  # 24 小时
        )

        return cache_manager.get_context_for_claude(cache_key)

    @staticmethod
    def record_api_usage(
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        cache_hit: bool = False,
    ) -> Dict[str, Any]:
        """
        记录 API 使用和成本

        Args:
            input_tokens: 输入 tokens
            output_tokens: 输出 tokens
            cache_read_tokens: 缓存读取 tokens
            cache_write_tokens: 缓存写入 tokens
            conversation_id: 对话 ID
            user_id: 用户 ID
            cache_hit: 是否缓存命中

        Returns:
            成本统计信息
        """
        cost_tracker = get_cost_tracker()

        # 记录调用
        record = cost_tracker.record_api_call(
            query_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            conversation_id=conversation_id,
            user_id=user_id,
            cache_hit=cache_hit,
        )

        # 同时记录到缓存管理器
        cache_manager = get_claude_cache_manager()

        if cache_read_tokens > 0:
            cache_manager.record_cache_hit(cache_read_tokens)
        if cache_write_tokens > 0:
            cache_manager.record_cache_write(cache_write_tokens)
        if not (cache_read_tokens or cache_write_tokens):
            cache_manager.record_cache_miss(input_tokens + output_tokens)

        logger.info(
            f"API usage recorded: "
            f"input={input_tokens}, output={output_tokens}, "
            f"cache_read={cache_read_tokens}, cache_write={cache_write_tokens}, "
            f"cost=${record.total_cost:.4f}"
        )

        return {
            "total_cost": record.total_cost,
            "cache_read_cost": record.cache_read_cost,
            "cache_write_cost": record.cache_write_cost,
            "saved_cost": record.saved_cost,
            "savings_percent": 90 if cache_hit else 0,
        }

    @staticmethod
    def build_claude_request_with_cache(
        system_prompt_type: str = "chat",
        messages: Optional[List[Dict[str, str]]] = None,
        conversation_id: Optional[str] = None,
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        构建带缓存的 Claude 请求

        Args:
            system_prompt_type: 系统提示类型
            messages: 消息列表
            conversation_id: 对话 ID (用于缓存上下文)
            additional_context: 额外的上下文

        Returns:
            Claude API 请求体
        """
        system_blocks = []

        # 添加缓存的系统提示
        cached_prompt = ClaudeAgentIntegration.get_cached_system_prompt(
            system_prompt_type
        )
        if cached_prompt:
            system_blocks.append(cached_prompt)

        # 添加缓存的对话上下文
        if conversation_id and messages:
            context_block = ClaudeAgentIntegration.cache_conversation_context(
                conversation_id=conversation_id,
                messages=messages,
            )
            if context_block:
                system_blocks.append(context_block)

        # 添加额外上下文
        if additional_context:
            system_blocks.append({
                "type": "text",
                "text": additional_context,
                "cache_control": {"type": "ephemeral"}
            })

        return {
            "system": system_blocks,
            "messages": messages or [],
        }

    @staticmethod
    def get_cache_statistics() -> Dict[str, Any]:
        """获取缓存统计信息"""
        cache_manager = get_claude_cache_manager()
        return cache_manager.get_cache_stats()

    @staticmethod
    def get_cost_summary() -> Dict[str, Any]:
        """获取成本摘要"""
        cost_tracker = get_cost_tracker()
        return cost_tracker.get_summary()


# 初始化函数，应该在应用启动时调用
def initialize_claude_integration():
    """初始化 Claude 集成"""
    ClaudeAgentIntegration.initialize_cache()
    logger.info("Claude integration initialized with caching support")
