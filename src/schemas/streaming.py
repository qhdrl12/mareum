"""
Streaming response schemas for LangGraph chunks.
LangGraph 청크를 위한 스트리밍 응답 스키마.
"""

import json
from typing import Optional
from dataclasses import dataclass
from enum import Enum
from langchain_core.messages import ToolMessage, AIMessageChunk


class ChunkType(str, Enum):
    """LangGraph 청크 타입 - 3가지 핵심 패턴"""
    TOOL_CALL = "tool_call"      # AIMessageChunk with tool_calls
    TOOL_MESSAGE = "tool_message"  # ToolMessage 
    CONTENT = "content"          # AIMessageChunk with content


@dataclass
class StreamChunk:
    """간단한 스트림 청크"""
    type: ChunkType
    data: str
    tool_name: Optional[str] = None
    
    def to_sse(self) -> str:
        """SSE 형태로 변환"""
        return f"data: {json.dumps({'type': self.type, 'data': self.data, 'tool': self.tool_name}, ensure_ascii=False)}\n\n"
    
    def to_json_line(self) -> str:
        """JSON Lines 형태로 변환"""
        return f"{json.dumps({'type': self.type, 'data': self.data, 'tool': self.tool_name}, ensure_ascii=False)}\n"


def parse_chunk(chunk) -> Optional[StreamChunk]:
    """
    LangGraph 청크를 3가지 핵심 패턴으로 파싱
    
    Args:
        chunk: LangGraph astream() 결과 (stream_mode에 따라 구조가 다름)
        
    Returns:
        StreamChunk 인스턴스 또는 None (파싱할 데이터가 없는 경우)
    """
    
    
    
    # stream_mode="messages"인 경우: (message, metadata) 튜플 형태
    if isinstance(chunk, tuple) and len(chunk) >= 2:
        message, _ = chunk[0], chunk[1]
        # print(f"message: {message}")
        
        # ToolMessage 인스턴스 확인
        if isinstance(message, ToolMessage):
            return StreamChunk(
                type=ChunkType.TOOL_MESSAGE,
                data=message.content,
                tool_name=message.name
            )
        # AIMessageChunk 인스턴스 확인
        elif isinstance(message, AIMessageChunk):
            # tool_call_chunks 확인 (스트리밍 중 부분적인 tool call)
            if hasattr(message, 'tool_call_chunks') and message.tool_call_chunks:
                # tool_call_chunks에서 유효한 정보가 있는지 확인
                for chunk in message.tool_call_chunks:
                    if chunk and (chunk.get('name') or chunk.get('args')):
                        return StreamChunk(
                            type=ChunkType.TOOL_CALL,
                            data=chunk.get('args', ''),
                            tool_name=chunk.get('name', 'unknown')
                        )
            
            # AIMessageChunk with content
            elif hasattr(message, 'content') and message.content:
                return StreamChunk(
                    type=ChunkType.CONTENT,
                    data=message.content
                )
    # 파싱할 데이터가 없음
    return None


async def langraph_to_sse_stream(langraph_chunks):
    """LangGraph 청크를 SSE로 변환 (유의미한 데이터만)"""
    async for chunk in langraph_chunks:
        parsed = parse_chunk(chunk)
        if parsed:  # None이 아닌 경우만 전송
            yield parsed.to_sse()


async def langraph_to_json_lines_stream(langraph_chunks):
    """LangGraph 청크를 JSON Lines로 변환 (유의미한 데이터만)"""
    async for chunk in langraph_chunks:
        parsed = parse_chunk(chunk)
        if parsed:  # None이 아닌 경우만 전송
            yield parsed.to_json_line() 