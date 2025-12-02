import asyncio
import json
import time
from typing import Optional, Dict, Any, List, AsyncGenerator, Callable
from dataclasses import dataclass, field
from enum import Enum
import structlog

from backend.app.services.guardrails_service import guardrails_service, GuardrailAction

logger = structlog.get_logger()


class StreamAction(str, Enum):
    CONTINUE = "continue"
    BLOCK = "block"
    REDACT = "redact"
    WARN = "warn"


@dataclass
class StreamInspectionResult:
    action: StreamAction
    triggered_rule: Optional[str] = None
    message: Optional[str] = None
    redacted_content: Optional[str] = None
    chunk_index: int = 0


@dataclass
class StreamBuffer:
    chunks: List[str] = field(default_factory=list)
    full_content: str = ""
    chunk_count: int = 0
    start_time: float = field(default_factory=time.time)
    last_inspection_index: int = 0
    blocked: bool = False
    block_reason: Optional[str] = None


class StreamInspectionService:
    def __init__(
        self,
        inspection_interval: int = 10,
        min_chars_for_inspection: int = 100,
        buffer_timeout_seconds: float = 30.0,
        enable_async_inspection: bool = True
    ):
        self.inspection_interval = inspection_interval
        self.min_chars_for_inspection = min_chars_for_inspection
        self.buffer_timeout_seconds = buffer_timeout_seconds
        self.enable_async_inspection = enable_async_inspection
        
        self._active_streams: Dict[str, StreamBuffer] = {}
        self._inspection_tasks: Dict[str, asyncio.Task] = {}
        
        logger.info(
            "stream_inspection_initialized",
            interval=inspection_interval,
            min_chars=min_chars_for_inspection
        )
    
    async def create_inspected_stream(
        self,
        stream: AsyncGenerator[str, None],
        request_id: str,
        tenant_id: int,
        model: str,
        on_violation: Optional[Callable[[StreamInspectionResult], None]] = None
    ) -> AsyncGenerator[str, None]:
        buffer = StreamBuffer()
        self._active_streams[request_id] = buffer
        
        try:
            chunk_index = 0
            
            async for chunk in stream:
                if buffer.blocked:
                    error_chunk = self._create_error_chunk(
                        buffer.block_reason or "Content blocked by guardrails"
                    )
                    yield error_chunk
                    yield "data: [DONE]\n\n"
                    break
                
                yield chunk
                
                content = self._extract_content_from_chunk(chunk)
                if content:
                    buffer.chunks.append(content)
                    buffer.full_content += content
                    buffer.chunk_count += 1
                    chunk_index += 1
                
                if self._should_inspect(buffer, chunk_index):
                    result = await self._inspect_buffer(buffer, tenant_id, chunk_index)
                    
                    if result.action == StreamAction.BLOCK:
                        buffer.blocked = True
                        buffer.block_reason = result.message
                        
                        if on_violation:
                            on_violation(result)
                        
                        error_chunk = self._create_error_chunk(result.message or "Content blocked")
                        yield error_chunk
                        yield "data: [DONE]\n\n"
                        break
                    
                    elif result.action == StreamAction.WARN and on_violation:
                        on_violation(result)
            
            if not buffer.blocked and buffer.full_content:
                final_result = await self._final_inspection(buffer, tenant_id)
                
                if final_result.action == StreamAction.BLOCK:
                    logger.warning(
                        "stream_blocked_at_end",
                        request_id=request_id,
                        reason=final_result.message
                    )
                    
                    if on_violation:
                        on_violation(final_result)
        
        finally:
            if request_id in self._active_streams:
                del self._active_streams[request_id]
            if request_id in self._inspection_tasks:
                self._inspection_tasks[request_id].cancel()
                del self._inspection_tasks[request_id]
    
    def _extract_content_from_chunk(self, chunk: str) -> Optional[str]:
        if not chunk.startswith("data: "):
            return None
        
        data = chunk[6:].strip()
        
        if data == "[DONE]":
            return None
        
        try:
            parsed = json.loads(data)
            choices = parsed.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                return delta.get("content", "")
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _should_inspect(self, buffer: StreamBuffer, chunk_index: int) -> bool:
        if buffer.blocked:
            return False
        
        chunks_since_inspection = chunk_index - buffer.last_inspection_index
        
        if chunks_since_inspection >= self.inspection_interval:
            if len(buffer.full_content) >= self.min_chars_for_inspection:
                return True
        
        return False
    
    async def _inspect_buffer(
        self,
        buffer: StreamBuffer,
        tenant_id: int,
        chunk_index: int
    ) -> StreamInspectionResult:
        buffer.last_inspection_index = chunk_index
        
        content_to_check = buffer.full_content
        
        result = guardrails_service.validate_output(content_to_check, tenant_id)
        
        if not result.passed:
            action = StreamAction.BLOCK if result.action == GuardrailAction.BLOCK else StreamAction.WARN
            
            logger.info(
                "stream_inspection_triggered",
                action=action.value,
                rule=result.triggered_rule,
                chunk_index=chunk_index
            )
            
            return StreamInspectionResult(
                action=action,
                triggered_rule=result.triggered_rule,
                message=result.message,
                chunk_index=chunk_index
            )
        
        return StreamInspectionResult(action=StreamAction.CONTINUE, chunk_index=chunk_index)
    
    async def _final_inspection(
        self,
        buffer: StreamBuffer,
        tenant_id: int
    ) -> StreamInspectionResult:
        if not buffer.full_content:
            return StreamInspectionResult(action=StreamAction.CONTINUE)
        
        result = guardrails_service.validate_output(buffer.full_content, tenant_id)
        
        if not result.passed:
            return StreamInspectionResult(
                action=StreamAction.BLOCK if result.action == GuardrailAction.BLOCK else StreamAction.WARN,
                triggered_rule=result.triggered_rule,
                message=result.message,
                chunk_index=buffer.chunk_count
            )
        
        return StreamInspectionResult(action=StreamAction.CONTINUE)
    
    def _create_error_chunk(self, message: str) -> str:
        error_data = {
            "error": {
                "message": message,
                "type": "guardrail_violation",
                "code": "content_blocked"
            }
        }
        return f"data: {json.dumps(error_data)}\n\n"
    
    def get_active_streams(self) -> Dict[str, Dict[str, Any]]:
        result = {}
        for request_id, buffer in self._active_streams.items():
            result[request_id] = {
                "chunk_count": buffer.chunk_count,
                "content_length": len(buffer.full_content),
                "elapsed_seconds": time.time() - buffer.start_time,
                "blocked": buffer.blocked,
                "last_inspection_index": buffer.last_inspection_index
            }
        return result
    
    async def force_stop_stream(self, request_id: str, reason: str = "Manually stopped"):
        if request_id in self._active_streams:
            buffer = self._active_streams[request_id]
            buffer.blocked = True
            buffer.block_reason = reason
            
            logger.info("stream_force_stopped", request_id=request_id, reason=reason)
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "active_streams": len(self._active_streams),
            "inspection_interval": self.inspection_interval,
            "min_chars_for_inspection": self.min_chars_for_inspection,
            "buffer_timeout_seconds": self.buffer_timeout_seconds
        }


stream_inspection_service = StreamInspectionService(
    inspection_interval=10,
    min_chars_for_inspection=100,
    buffer_timeout_seconds=30.0
)
