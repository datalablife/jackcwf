"""
流式聊天服务

实现服务器推送事件 (Server-Sent Events) 的流式 LLM 响应。
目标: 首字节延迟 <100ms, 块吞吐量 >50/sec
"""

import asyncio
import time
import logging
from typing import AsyncGenerator, Optional, List
from datetime import datetime

from src.models.streaming_models import (
    StreamEvent,
    MessageChunkEvent,
    ToolCallEvent,
    ToolResultEvent,
    ThinkingEvent,
    CompleteStateEvent,
    ErrorEvent,
    StreamEventType,
    StreamingConfig,
)

logger = logging.getLogger(__name__)


class StreamingChatService:
    """
    流式聊天服务

    通过 Server-Sent Events 提供实时流式 LLM 响应。
    """

    def __init__(
        self,
        config: Optional[StreamingConfig] = None,
    ):
        """
        初始化流式聊天服务

        Args:
            config: 流式响应配置
        """
        self.config = config or StreamingConfig()
        self.active_connections = {}
        self.start_time = time.time()

    async def stream_conversation_response(
        self,
        conversation_id: str,
        user_id: str,
        user_message: str,
        include_thinking: bool = False,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        流式生成对话响应

        这是核心的流式处理方法。

        Args:
            conversation_id: 对话 ID
            user_id: 用户 ID
            user_message: 用户消息内容
            include_thinking: 是否包含思考过程

        Yields:
            StreamEvent: 流式事件

        Performance Targets:
            - First byte latency: <100ms
            - Chunk throughput: >50 chunks/sec
            - Memory per connection: <20MB
        """

        connection_id = f"{user_id}:{conversation_id}:{time.time()}"
        sequence = 0

        try:
            # 记录连接
            self.active_connections[connection_id] = {
                "start_time": time.time(),
                "user_id": user_id,
                "conversation_id": conversation_id,
            }

            stream_start = time.time()

            # Step 1: 加载对话历史 (应该缓存)
            logger.debug(f"Loading conversation history for {conversation_id}")
            # messages = await self._load_conversation_messages(conversation_id)
            messages = []  # TODO: 从数据库加载

            # Step 2: 执行 LLM 流式生成
            accumulated_text = ""
            chunk_count = 0
            tool_calls = 0
            first_event_sent = False

            # 模拟流式生成 (实际应该调用 LangChain Agent)
            # 这里我们实现一个演示版本
            demo_response = (
                "Hello! I'll help you with that. "
                "Let me search for relevant information "
                "and provide a comprehensive answer."
            )

            # 分块发送响应
            words = demo_response.split()
            for i, word in enumerate(words):
                # 累积文本直到达到缓冲区大小
                accumulated_text += word + " "

                # 每 5 个词或最后一个词时发送块
                if (i + 1) % 5 == 0 or i == len(words) - 1:
                    # 首字节延迟优化: 快速发送第一个事件
                    if not first_event_sent:
                        first_event_time = (time.time() - stream_start) * 1000
                        logger.info(f"First byte latency: {first_event_time:.1f}ms")
                        first_event_sent = True

                    # 发送消息块事件
                    chunk_event = MessageChunkEvent(
                        type=StreamEventType.MESSAGE_CHUNK,
                        timestamp=time.time(),
                        sequence=sequence,
                        content=accumulated_text.strip(),
                        token_count=len(accumulated_text.split()),
                        is_final=(i == len(words) - 1),
                    )
                    sequence += 1
                    chunk_count += 1
                    yield chunk_event

                    # 清除累积文本
                    accumulated_text = ""

                    # 模拟网络延迟 (实际上由网络决定)
                    await asyncio.sleep(0.01)

            # Step 3: 发送完成状态事件
            elapsed_time = time.time() - stream_start
            complete_event = CompleteStateEvent(
                type=StreamEventType.COMPLETE_STATE,
                timestamp=time.time(),
                sequence=sequence,
                final_message=demo_response,
                total_tokens=len(demo_response.split()),
                total_chunks=chunk_count,
                elapsed_time=elapsed_time,
                tool_calls_count=tool_calls,
                cache_hit=False,
            )
            sequence += 1
            yield complete_event

            logger.info(
                f"Stream completed: conversation_id={conversation_id}, "
                f"chunks={chunk_count}, tokens={len(demo_response.split())}, "
                f"elapsed={elapsed_time:.2f}s"
            )

        except asyncio.CancelledError:
            logger.warning(f"Stream cancelled: {connection_id}")
            # 不需要发送错误事件，连接已断开
            raise

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            # 发送错误事件
            error_event = ErrorEvent(
                type=StreamEventType.ERROR,
                timestamp=time.time(),
                sequence=sequence,
                error_code="STREAM_PROCESSING_ERROR",
                error_message=str(e),
                recoverable=False,
            )
            yield error_event

        finally:
            # 清理连接
            if connection_id in self.active_connections:
                duration = time.time() - self.active_connections[connection_id]["start_time"]
                logger.debug(f"Connection closed: {connection_id}, duration={duration:.2f}s")
                del self.active_connections[connection_id]

    async def stream_with_tool_calls(
        self,
        conversation_id: str,
        user_id: str,
        user_message: str,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        流式生成带工具调用的响应

        演示工具调用的流式传输。
        """

        sequence = 0

        try:
            # 发送初始思考事件
            if True:  # include_thinking
                thinking_event = ThinkingEvent(
                    type=StreamEventType.THINKING,
                    timestamp=time.time(),
                    sequence=sequence,
                    thought="I should search for information first",
                    reasoning="The user asked a question that requires current information",
                )
                sequence += 1
                yield thinking_event
                await asyncio.sleep(0.05)

            # 发送工具调用事件
            tool_event = ToolCallEvent(
                type=StreamEventType.TOOL_CALL,
                timestamp=time.time(),
                sequence=sequence,
                tool_name="search",
                tool_input={"query": user_message},
            )
            sequence += 1
            yield tool_event
            await asyncio.sleep(0.1)

            # 模拟工具执行 (实际上由 Agent 执行)
            await asyncio.sleep(0.5)

            # 发送工具结果事件
            result_event = ToolResultEvent(
                type=StreamEventType.TOOL_RESULT,
                timestamp=time.time(),
                sequence=sequence,
                tool_name="search",
                result="Found 5 relevant articles about the topic",
                is_error=False,
            )
            sequence += 1
            yield result_event

            # 发送响应文本块
            response = "Based on the search results, here's what I found..."
            for i, chunk in enumerate(response.split()):
                chunk_event = MessageChunkEvent(
                    type=StreamEventType.MESSAGE_CHUNK,
                    timestamp=time.time(),
                    sequence=sequence,
                    content=chunk,
                    token_count=1,
                    is_final=(i == len(response.split()) - 1),
                )
                sequence += 1
                yield chunk_event
                await asyncio.sleep(0.01)

            # 发送完成状态
            complete_event = CompleteStateEvent(
                type=StreamEventType.COMPLETE_STATE,
                timestamp=time.time(),
                sequence=sequence,
                final_message=response,
                total_tokens=len(response.split()),
                total_chunks=len(response.split()),
                elapsed_time=1.5,
                tool_calls_count=1,
                cache_hit=False,
            )
            yield complete_event

        except Exception as e:
            logger.error(f"Tool call streaming error: {e}", exc_info=True)
            error_event = ErrorEvent(
                type=StreamEventType.ERROR,
                timestamp=time.time(),
                sequence=sequence,
                error_code="TOOL_CALL_STREAMING_ERROR",
                error_message=str(e),
                recoverable=True,
            )
            yield error_event

    async def _load_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 10,
    ) -> List[dict]:
        """
        加载对话消息历史

        Args:
            conversation_id: 对话 ID
            limit: 最大消息数

        Returns:
            消息列表
        """
        # TODO: 从数据库加载
        return []

    def get_active_connections_count(self) -> int:
        """获取活跃连接数"""
        return len(self.active_connections)

    def get_uptime_seconds(self) -> float:
        """获取服务运行时间"""
        return time.time() - self.start_time

    async def cleanup_stale_connections(self, timeout_seconds: float = 300):
        """
        清理超时的连接

        Args:
            timeout_seconds: 超时时间 (秒)
        """
        current_time = time.time()
        stale_connections = []

        for conn_id, conn_info in self.active_connections.items():
            if current_time - conn_info["start_time"] > timeout_seconds:
                stale_connections.append(conn_id)

        for conn_id in stale_connections:
            logger.warning(f"Cleaning up stale connection: {conn_id}")
            del self.active_connections[conn_id]

        return len(stale_connections)
