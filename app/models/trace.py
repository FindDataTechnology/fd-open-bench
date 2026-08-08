"""Trace and Span data models for agent execution tracking."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, JSON, Text
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class TokenUsage(BaseModel):
    """Token usage statistics for a span."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    model: Optional[str] = None
    estimated_cost: Optional[float] = None


class Span(BaseModel):
    """Individual execution span in a trace."""
    span_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_span_id: Optional[str] = None
    span_type: str  # 'agent', 'llm', 'tool', 'retriever'
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    input: Optional[str] = None
    output: Optional[str] = None
    token_usage: Optional[TokenUsage] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: str = "success"  # 'success', 'error', 'timeout'
    error_message: Optional[str] = None

    def calculate_duration(self) -> float:
        """Calculate duration in milliseconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary."""
        return {
            'span_id': self.span_id,
            'parent_span_id': self.parent_span_id,
            'span_type': self.span_type,
            'name': self.name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_ms': self.duration_ms,
            'input': self.input,
            'output': self.output,
            'token_usage': self.token_usage.dict() if self.token_usage else None,
            'metadata': self.metadata,
            'status': self.status,
            'error_message': self.error_message
        }


class Trace(BaseModel):
    """Complete execution trace for an agent run."""
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    agent_id: str
    root_span_id: Optional[str] = None
    spans: List[Span] = Field(default_factory=list)
    total_duration_ms: Optional[float] = None
    total_tokens: Optional[int] = None
    total_cost: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def add_span(self, span: Span) -> None:
        """Add a span to the trace."""
        self.spans.append(span)
        if span.parent_span_id is None:
            self.root_span_id = span.span_id

    def calculate_totals(self) -> None:
        """Calculate total duration, tokens, and cost."""
        # Calculate total duration from root span
        if self.root_span_id:
            root_span = next((s for s in self.spans if s.span_id == self.root_span_id), None)
            if root_span and root_span.duration_ms:
                self.total_duration_ms = root_span.duration_ms

        # Sum up tokens and costs
        total_input = 0
        total_output = 0
        total_cost = 0.0

        for span in self.spans:
            if span.token_usage:
                total_input += span.token_usage.input_tokens
                total_output += span.token_usage.output_tokens
                if span.token_usage.estimated_cost:
                    total_cost += span.token_usage.estimated_cost

        self.total_tokens = total_input + total_output
        self.total_cost = total_cost

    def get_span_tree(self) -> Dict[str, Any]:
        """Get hierarchical span tree structure."""
        span_map = {span.span_id: span for span in self.spans}
        tree = []

        def build_tree(span_id: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
            span = span_map.get(span_id)
            if not span:
                return {}

            node = span.to_dict()
            children = [s for s in self.spans if s.parent_span_id == span_id]
            node['children'] = [build_tree(c.span_id, span_id) for c in children]
            return node

        if self.root_span_id:
            tree = [build_tree(self.root_span_id)]
        else:
            # No root span, build forest
            root_spans = [s for s in self.spans if s.parent_span_id is None]
            tree = [build_tree(s.span_id) for s in root_spans]

        return {'trace_id': self.trace_id, 'spans': tree}

    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary."""
        return {
            'trace_id': self.trace_id,
            'run_id': self.run_id,
            'agent_id': self.agent_id,
            'root_span_id': self.root_span_id,
            'spans': [span.to_dict() for span in self.spans],
            'total_duration_ms': self.total_duration_ms,
            'total_tokens': self.total_tokens,
            'total_cost': self.total_cost,
            'created_at': self.created_at.isoformat()
        }


class TraceDB(Base):
    """Database model for trace storage."""
    __tablename__ = "traces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id = Column(String(36), unique=True, nullable=False, index=True)
    run_id = Column(String(36), ForeignKey("evaluation_runs.id"), nullable=False, index=True)
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False, index=True)
    root_span_id = Column(String(36), nullable=True)
    total_duration_ms = Column(Float, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    total_cost = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    run = relationship("EvaluationRun", back_populates="trace")
    agent = relationship("Agent")
