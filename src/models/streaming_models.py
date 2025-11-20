"""
流式响应数据模型

定义所有流式事件类型和数据结构，支持实时 Server-Sent Events 传输。
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class StreamEventType(str, Enum):
    """流式事件类型枚举"""
    MESSAGE_CHUNK = "message_chunk"        # 文本消息块
    TOOL_CALL = "tool_call"                # 工具调用事件
    TOOL_RESULT = "tool_result"            # 工具执行结果
    THINKING = "thinking"                  # 思考过程
    COMPLETE_STATE = "complete_state"      # 响应完成状态
    ERROR = "error"                        # 错误事件


class StreamEvent(BaseModel):
    """
    基础流式事件模型

    所有流式事件的基类，包含通用字段。
    """
    type: StreamEventType                  # 事件类型
    timestamp: float = Field(default_factory=lambda: datetime.utcnow().timestamp())
    sequence: int                          # 事件序列号


class MessageChunkEvent(StreamEvent):
    """
    消息块事件

    LLM 生成的文本块，按流式方式发送。
    """
    type: StreamEventType = StreamEventType.MESSAGE_CHUNK
    content: str = Field(..., description="文本块内容 (50-100 tokens)")
    token_count: int = Field(..., description="该块的 token 数")
    is_final: bool = Field(default=False, description="是否为最后一块")

    class Config:
        """Pydantic 配置"""
        json_schema_extra = {
            "example": {
                "type": "message_chunk",
                "timestamp": 1700000000.123,
                "sequence": 0,
                "content": "Hello, this is a streamed response...",
                "token_count": 8,
                "is_final": False
            }
        }


class ToolCallEvent(StreamEvent):
    """
    工具调用事件

    Agent 调用外部工具时发送。
    """
    type: StreamEventType = StreamEventType.TOOL_CALL
    tool_name: str = Field(..., description="工具名称 (e.g., 'search', 'calculator')")
    tool_input: Dict[str, Any] = Field(..., description="工具的输入参数")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "tool_call",
                "timestamp": 1700000000.456,
                "sequence": 5,
                "tool_name": "search",
                "tool_input": {"query": "Python async programming"}
            }
        }


class ToolResultEvent(StreamEvent):
    """
    工具执行结果事件

    工具执行完成后发送结果。
    """
    type: StreamEventType = StreamEventType.TOOL_RESULT
    tool_name: str = Field(..., description="执行的工具名称")
    result: Any = Field(..., description="工具执行结果")
    is_error: bool = Field(default=False, description="是否为错误结果")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "tool_result",
                "timestamp": 1700000000.789,
                "sequence": 6,
                "tool_name": "search",
                "result": "Found 5 relevant articles about async programming",
                "is_error": False
            }
        }


class ThinkingEvent(StreamEvent):
    """
    思考过程事件 (可选)

    显示 Agent 的中间思考过程。
    """
    type: StreamEventType = StreamEventType.THINKING
    thought: str = Field(..., description="思考内容")
    reasoning: Optional[str] = Field(default=None, description="推理过程")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "thinking",
                "timestamp": 1700000000.234,
                "sequence": 1,
                "thought": "I need to search for information first",
                "reasoning": "The user asked about Python async programming"
            }
        }


class CompleteStateEvent(StreamEvent):
    """
    完成状态事件

    响应流完成时发送，包含汇总统计信息。
    """
    type: StreamEventType = StreamEventType.COMPLETE_STATE
    final_message: str = Field(..., description="最终完整消息")
    total_tokens: int = Field(..., description="总生成 token 数")
    total_chunks: int = Field(..., description="总块数")
    elapsed_time: float = Field(..., description="总耗时 (秒)")
    tool_calls_count: int = Field(default=0, description="工具调用次数")
    cache_hit: bool = Field(default=False, description="是否命中缓存")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "complete_state",
                "timestamp": 1700000001.234,
                "sequence": 10,
                "final_message": "Based on my search...",
                "total_tokens": 150,
                "total_chunks": 3,
                "elapsed_time": 2.345,
                "tool_calls_count": 1,
                "cache_hit": False
            }
        }


class ErrorEvent(StreamEvent):
    """
    错误事件

    流处理过程中发生错误时发送。
    """
    type: StreamEventType = StreamEventType.ERROR
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误详细信息")
    recoverable: bool = Field(default=False, description="是否可恢复")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "error",
                "timestamp": 1700000000.999,
                "sequence": 3,
                "error_code": "TOOL_EXECUTION_FAILED",
                "error_message": "Search tool failed: connection timeout",
                "recoverable": True
            }
        }


# 联合类型：所有可能的流式事件
StreamingEventUnion = (
    MessageChunkEvent |
    ToolCallEvent |
    ToolResultEvent |
    ThinkingEvent |
    CompleteStateEvent |
    ErrorEvent
)


# 用于客户端的流式请求模型
class StreamChatRequest(BaseModel):
    """流式聊天请求"""
    message: str = Field(..., description="用户消息", min_length=1, max_length=4000)
    include_thinking: bool = Field(default=False, description="是否包含思考过程")
    context_window: int = Field(default=10, description="消息历史窗口大小")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What is the best practice for Python async programming?",
                "include_thinking": False,
                "context_window": 10
            }
        }


# 流式响应配置
class StreamingConfig(BaseModel):
    """流式响应配置"""
    chunk_size: int = Field(default=50, description="每个块的平均 token 数")
    buffer_timeout: float = Field(default=0.5, description="缓冲区超时 (秒)")
    max_connections: int = Field(default=100, description="最大并发连接数")
    enable_metrics: bool = Field(default=True, description="是否启用监控指标")
    first_byte_target_ms: int = Field(default=100, description="首字节延迟目标 (ms)")
    chunk_throughput_target: int = Field(default=50, description="目标块吞吐量 (chunks/sec)")

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_size": 50,
                "buffer_timeout": 0.5,
                "max_connections": 100,
                "enable_metrics": True,
                "first_byte_target_ms": 100,
                "chunk_throughput_target": 50
            }
        }
