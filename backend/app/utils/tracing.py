"""
Financial Intelligence Platform — Request Tracing

Generates and propagates trace IDs across the entire request lifecycle.
Every tool call, database query, model invocation, and response can be
traced back to a single request using the trace_id.

This is non-negotiable. If you can't answer "why did the system produce
this response?", the system has failed.
"""

import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# Request-scoped trace context
_trace_context: ContextVar["TraceContext | None"] = ContextVar(
    "trace_context", default=None
)


@dataclass
class TraceSpan:
    """A single span within a trace — represents one operation."""

    span_id: str
    operation: str  # e.g., "tool:get_price", "db:query", "model:gemini"
    started_at: datetime
    ended_at: datetime | None = None
    duration_ms: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    status: str = "ok"  # ok | error

    def finish(self, error: str | None = None) -> None:
        """Mark span as complete."""
        self.ended_at = datetime.now(timezone.utc)
        self.duration_ms = int(
            (self.ended_at - self.started_at).total_seconds() * 1000
        )
        if error:
            self.error = error
            self.status = "error"


@dataclass
class TraceContext:
    """Full trace context for a request — contains all spans."""

    trace_id: str
    user_id: str | None = None
    query: str | None = None
    started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    spans: list[TraceSpan] = field(default_factory=list)

    def start_span(self, operation: str, **metadata: Any) -> TraceSpan:
        """Start a new span within this trace."""
        span = TraceSpan(
            span_id=str(uuid.uuid4())[:8],
            operation=operation,
            started_at=datetime.now(timezone.utc),
            metadata=metadata,
        )
        self.spans.append(span)
        return span

    @property
    def total_duration_ms(self) -> int | None:
        """Total trace duration in milliseconds."""
        if not self.spans:
            return None
        last_span = max(
            (s for s in self.spans if s.ended_at),
            key=lambda s: s.ended_at,
            default=None,
        )
        if last_span and last_span.ended_at:
            return int(
                (last_span.ended_at - self.started_at).total_seconds() * 1000
            )
        return None

    @property
    def tool_calls(self) -> list[TraceSpan]:
        """All tool call spans in this trace."""
        return [s for s in self.spans if s.operation.startswith("tool:")]

    @property
    def has_errors(self) -> bool:
        """Whether any span in the trace has an error."""
        return any(s.status == "error" for s in self.spans)

    def to_dict(self) -> dict[str, Any]:
        """Serialize trace for storage/logging."""
        return {
            "trace_id": self.trace_id,
            "user_id": self.user_id,
            "query": self.query,
            "started_at": self.started_at.isoformat(),
            "total_duration_ms": self.total_duration_ms,
            "span_count": len(self.spans),
            "has_errors": self.has_errors,
            "spans": [
                {
                    "span_id": s.span_id,
                    "operation": s.operation,
                    "duration_ms": s.duration_ms,
                    "status": s.status,
                    "error": s.error,
                    "metadata": s.metadata,
                }
                for s in self.spans
            ],
        }


def create_trace(
    user_id: str | None = None, query: str | None = None
) -> TraceContext:
    """Create a new trace context and set it as the current context."""
    ctx = TraceContext(
        trace_id=str(uuid.uuid4())[:8],
        user_id=user_id,
        query=query,
    )
    _trace_context.set(ctx)
    return ctx


def get_current_trace() -> TraceContext | None:
    """Get the current trace context."""
    return _trace_context.get()


def start_span(operation: str, **metadata: Any) -> TraceSpan:
    """Start a span in the current trace. Creates trace if none exists."""
    ctx = get_current_trace()
    if ctx is None:
        ctx = create_trace()
    return ctx.start_span(operation, **metadata)
