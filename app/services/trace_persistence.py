"""Trace persistence and retrieval service."""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.trace import Trace, TraceDB, Span, TokenUsage
from app.utils.compression import compress_trace, decompress_trace


class TracePersistenceService:
    """Service for persisting and retrieving traces."""

    def __init__(self, db: Session):
        self.db = db

    def save_trace(self, trace: Trace) -> str:
        """Save trace to database with compression.

        Args:
            trace: The trace to save

        Returns:
            The trace ID
        """
        # Compress the trace data
        trace_data = trace.to_dict()
        compressed_data = compress_trace(trace_data)

        # Create database record
        trace_db = TraceDB(
            trace_id=trace.trace_id,
            run_id=trace.run_id,
            agent_id=trace.agent_id,
            root_span_id=trace.root_span_id,
            total_duration_ms=trace.total_duration_ms,
            total_tokens=trace.total_tokens,
            total_cost=trace.total_cost,
            created_at=trace.created_at
        )

        # Store compressed data in a separate table or field
        # For now, we'll use a JSON field that stores the compressed hex
        trace_db.compressed_trace = compressed_data

        self.db.add(trace_db)
        self.db.commit()
        self.db.refresh(trace_db)

        return trace_db.trace_id

    def get_trace_by_id(self, trace_id: str) -> Optional[Trace]:
        """Retrieve trace by ID and decompress.

        Args:
            trace_id: The trace ID to retrieve

        Returns:
            The decompressed Trace object, or None if not found
        """
        trace_db = self.db.query(TraceDB).filter(TraceDB.trace_id == trace_id).first()

        if not trace_db:
            return None

        return self._decompress_trace_db(trace_db)

    def get_trace_by_run_id(self, run_id: str) -> Optional[Trace]:
        """Retrieve trace by run ID and decompress.

        Args:
            run_id: The run ID to retrieve trace for

        Returns:
            The decompressed Trace object, or None if not found
        """
        trace_db = self.db.query(TraceDB).filter(TraceDB.run_id == run_id).first()

        if not trace_db:
            return None

        return self._decompress_trace_db(trace_db)

    def list_traces(
        self,
        agent_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[Dict[str, Any]]:
        """List traces with optional filters.

        Args:
            agent_id: Filter by agent ID
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of trace metadata dictionaries
        """
        query = self.db.query(TraceDB)

        if agent_id:
            query = query.filter(TraceDB.agent_id == agent_id)

        if start_date:
            query = query.filter(TraceDB.created_at >= start_date)

        if end_date:
            query = query.filter(TraceDB.created_at <= end_date)

        query = query.order_by(TraceDB.created_at.desc())
        query = query.offset(offset).limit(limit)

        traces = query.all()

        return [
            {
                'trace_id': t.trace_id,
                'run_id': t.run_id,
                'agent_id': t.agent_id,
                'total_duration_ms': t.total_duration_ms,
                'total_tokens': t.total_tokens,
                'total_cost': t.total_cost,
                'created_at': t.created_at.isoformat()
            }
            for t in traces
        ]

    def delete_trace(self, trace_id: str) -> bool:
        """Delete a trace from the database.

        Args:
            trace_id: The trace ID to delete

        Returns:
            True if deleted, False if not found
        """
        trace_db = self.db.query(TraceDB).filter(TraceDB.trace_id == trace_id).first()

        if not trace_db:
            return False

        self.db.delete(trace_db)
        self.db.commit()
        return True

    def _decompress_trace_db(self, trace_db: TraceDB) -> Trace:
        """Decompress a TraceDB record into a Trace object.

        Args:
            trace_db: The database record

        Returns:
            The decompressed Trace object
        """
        # Decompress the trace data
        trace_data = decompress_trace(trace_db.compressed_trace)

        # Reconstruct Trace object
        trace = Trace(
            trace_id=trace_data['trace_id'],
            run_id=trace_data['run_id'],
            agent_id=trace_data['agent_id'],
            root_span_id=trace_data.get('root_span_id'),
            total_duration_ms=trace_data.get('total_duration_ms'),
            total_tokens=trace_data.get('total_tokens'),
            total_cost=trace_data.get('total_cost'),
            created_at=datetime.fromisoformat(trace_data['created_at'])
        )

        # Reconstruct spans
        for span_data in trace_data.get('spans', []):
            token_usage = None
            if span_data.get('token_usage'):
                token_usage = TokenUsage(**span_data['token_usage'])

            span = Span(
                span_id=span_data['span_id'],
                parent_span_id=span_data.get('parent_span_id'),
                span_type=span_data['span_type'],
                name=span_data['name'],
                start_time=datetime.fromisoformat(span_data['start_time']),
                end_time=datetime.fromisoformat(span_data['end_time']) if span_data.get('end_time') else None,
                duration_ms=span_data.get('duration_ms'),
                input=span_data.get('input'),
                output=span_data.get('output'),
                token_usage=token_usage,
                metadata=span_data.get('metadata', {}),
                status=span_data.get('status', 'success'),
                error_message=span_data.get('error_message')
            )
            trace.spans.append(span)

        return trace


class TraceExportService:
    """Service for exporting traces in various formats."""

    def __init__(self, db: Session):
        self.db = db
        self.persistence = TracePersistenceService(db)

    def export_as_json(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Export trace as JSON (DeepEval native format).

        Args:
            trace_id: The trace ID to export

        Returns:
            JSON dictionary representation, or None if not found
        """
        trace = self.persistence.get_trace_by_id(trace_id)

        if not trace:
            return None

        return self.export_trace_as_json(trace)

    def export_trace_as_json(self, trace: Trace) -> Dict[str, Any]:
        """Export an in-memory trace as JSON (DeepEval native format)."""
        return trace.to_dict()

    def export_as_opentelemetry(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Export trace in OpenTelemetry format (OTLP).

        Args:
            trace_id: The trace ID to export

        Returns:
            OpenTelemetry format dictionary, or None if not found
        """
        trace = self.persistence.get_trace_by_id(trace_id)

        if not trace:
            return None

        return self.export_trace_as_opentelemetry(trace)

    def export_trace_as_opentelemetry(self, trace: Trace) -> Dict[str, Any]:
        """Export an in-memory trace in OpenTelemetry format (OTLP)."""
        # Convert to OpenTelemetry format
        otel_trace = {
            'resourceSpans': [
                {
                    'resource': {
                        'attributes': [
                            {
                                'key': 'service.name',
                                'value': {'stringValue': 'fd-open-bench'}
                            },
                            {
                                'key': 'agent.id',
                                'value': {'stringValue': trace.agent_id}
                            },
                            {
                                'key': 'run.id',
                                'value': {'stringValue': trace.run_id}
                            }
                        ]
                    },
                    'scopeSpans': [
                        {
                            'scope': {
                                'name': 'fd-open-bench',
                                'version': '1.0.0'
                            },
                            'spans': self._convert_spans_to_otel(trace.spans)
                        }
                    ]
                }
            ]
        }

        return otel_trace

    def _convert_spans_to_otel(self, spans: list[Span]) -> list[Dict[str, Any]]:
        """Convert spans to OpenTelemetry format.

        Args:
            spans: List of spans to convert

        Returns:
            List of OpenTelemetry span dictionaries
        """
        otel_spans = []

        for span in spans:
            start_nano = int(span.start_time.timestamp() * 1e9)
            if span.end_time:
                end_nano = int(span.end_time.timestamp() * 1e9)
            else:
                # Injected/remote spans may only carry duration_ms
                end_nano = start_nano + int((span.duration_ms or 0) * 1e6)
            otel_span = {
                'traceId': span.span_id,  # Using span_id as traceId for simplicity
                'spanId': span.span_id,
                'parentSpanId': span.parent_span_id or '',
                'name': span.name,
                'kind': self._map_span_kind(span.span_type),
                'startTimeUnixNano': start_nano,
                'endTimeUnixNano': end_nano,
                'attributes': self._build_otel_attributes(span),
                'status': {
                    'code': 0 if span.status == 'success' else 2,
                    'message': span.error_message or ''
                }
            }

            otel_spans.append(otel_span)

        return otel_spans

    def _map_span_kind(self, span_type: str) -> int:
        """Map span type to OpenTelemetry span kind.

        Args:
            span_type: The span type (agent, llm, tool, retriever)

        Returns:
            OpenTelemetry span kind integer
        """
        kind_map = {
            'agent': 1,      # INTERNAL
            'llm': 3,        # CLIENT
            'tool': 3,       # CLIENT
            'retriever': 3   # CLIENT
        }
        return kind_map.get(span_type, 1)

    def _build_otel_attributes(self, span: Span) -> list[Dict[str, Any]]:
        """Build OpenTelemetry attributes from span data.

        Args:
            span: The span to build attributes for

        Returns:
            List of OpenTelemetry attribute dictionaries
        """
        attributes = [
            {
                'key': 'span.type',
                'value': {'stringValue': span.span_type}
            },
            {
                'key': 'span.status',
                'value': {'stringValue': span.status}
            }
        ]

        if span.input:
            attributes.append({
                'key': 'span.input',
                'value': {'stringValue': span.input}
            })

        if span.output:
            attributes.append({
                'key': 'span.output',
                'value': {'stringValue': span.output}
            })

        if span.duration_ms:
            attributes.append({
                'key': 'span.duration_ms',
                'value': {'doubleValue': span.duration_ms}
            })

        if span.token_usage:
            attributes.extend([
                {
                    'key': 'llm.input_tokens',
                    'value': {'intValue': str(span.token_usage.input_tokens)}
                },
                {
                    'key': 'llm.output_tokens',
                    'value': {'intValue': str(span.token_usage.output_tokens)}
                },
                {
                    'key': 'llm.total_tokens',
                    'value': {'intValue': str(span.token_usage.total_tokens)}
                }
            ])

            if span.token_usage.model:
                attributes.append({
                    'key': 'llm.model',
                    'value': {'stringValue': span.token_usage.model}
                })

            if span.token_usage.estimated_cost:
                attributes.append({
                    'key': 'llm.estimated_cost',
                    'value': {'doubleValue': span.token_usage.estimated_cost}
                })

        # Add metadata as attributes
        for key, value in span.metadata.items():
            if isinstance(value, str):
                attributes.append({
                    'key': f'metadata.{key}',
                    'value': {'stringValue': value}
                })
            elif isinstance(value, (int, float)):
                attributes.append({
                    'key': f'metadata.{key}',
                    'value': {'doubleValue': float(value)}
                })

        return attributes
