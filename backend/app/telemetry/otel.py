import os
import time
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager
from functools import wraps

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger()

_tracer: Optional[trace.Tracer] = None
_meter: Optional[metrics.Meter] = None
_initialized = False

llm_request_counter = None
llm_token_counter = None
llm_latency_histogram = None
llm_cost_counter = None
cache_hit_counter = None
guardrail_trigger_counter = None


def init_telemetry(
    service_name: str = "ai-gateway",
    service_version: str = "1.0.0",
    otlp_endpoint: Optional[str] = None,
    enable_console_export: bool = False
):
    global _tracer, _meter, _initialized
    global llm_request_counter, llm_token_counter, llm_latency_histogram
    global llm_cost_counter, cache_hit_counter, guardrail_trigger_counter
    
    if _initialized:
        return
    
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        "service.namespace": "bfsi-ai-gateway"
    })
    
    trace_provider = TracerProvider(resource=resource)
    
    if otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info("otel_traces_configured", endpoint=otlp_endpoint)
    
    if enable_console_export:
        trace_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    
    trace.set_tracer_provider(trace_provider)
    _tracer = trace.get_tracer(service_name, service_version)
    
    metric_readers = []
    
    if otlp_endpoint:
        otlp_metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
        metric_readers.append(PeriodicExportingMetricReader(otlp_metric_exporter, export_interval_millis=30000))
        logger.info("otel_metrics_configured", endpoint=otlp_endpoint)
    
    if enable_console_export:
        metric_readers.append(PeriodicExportingMetricReader(ConsoleMetricExporter(), export_interval_millis=60000))
    
    if not metric_readers:
        metric_readers.append(PeriodicExportingMetricReader(ConsoleMetricExporter(), export_interval_millis=300000))
    
    meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
    metrics.set_meter_provider(meter_provider)
    _meter = metrics.get_meter(service_name, service_version)
    
    llm_request_counter = _meter.create_counter(
        name="llm.requests.total",
        description="Total number of LLM requests",
        unit="1"
    )
    
    llm_token_counter = _meter.create_counter(
        name="llm.tokens.total",
        description="Total tokens consumed",
        unit="tokens"
    )
    
    llm_latency_histogram = _meter.create_histogram(
        name="llm.request.latency",
        description="LLM request latency in milliseconds",
        unit="ms"
    )
    
    llm_cost_counter = _meter.create_counter(
        name="llm.cost.total",
        description="Total cost of LLM requests in USD",
        unit="USD"
    )
    
    cache_hit_counter = _meter.create_counter(
        name="semantic_cache.hits.total",
        description="Total semantic cache hits",
        unit="1"
    )
    
    guardrail_trigger_counter = _meter.create_counter(
        name="guardrails.triggers.total",
        description="Total guardrail triggers",
        unit="1"
    )
    
    _initialized = True
    logger.info("opentelemetry_initialized", service=service_name, version=service_version)


def get_tracer() -> trace.Tracer:
    global _tracer
    if _tracer is None:
        init_telemetry()
    return _tracer  # type: ignore


def get_meter() -> metrics.Meter:
    global _meter
    if _meter is None:
        init_telemetry()
    return _meter  # type: ignore


@contextmanager
def create_span(
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None
):
    tracer = get_tracer()
    with tracer.start_as_current_span(name, kind=kind) as span:
        if attributes:
            for key, value in attributes.items():
                if value is not None:
                    span.set_attribute(key, str(value) if not isinstance(value, (int, float, bool)) else value)
        try:
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def record_llm_metrics(
    model: str,
    provider: str,
    tenant_id: int,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    latency_ms: float = 0,
    cost: float = 0,
    cache_hit: bool = False,
    status: str = "success",
    guardrail_triggered: Optional[str] = None
):
    attributes = {
        "model": model,
        "provider": provider,
        "tenant_id": str(tenant_id),
        "status": status
    }
    
    if llm_request_counter:
        llm_request_counter.add(1, attributes)
    
    if llm_token_counter:
        llm_token_counter.add(prompt_tokens, {**attributes, "token_type": "prompt"})
        llm_token_counter.add(completion_tokens, {**attributes, "token_type": "completion"})
    
    if llm_latency_histogram and latency_ms > 0:
        llm_latency_histogram.record(latency_ms, attributes)
    
    if llm_cost_counter and cost > 0:
        llm_cost_counter.add(cost, attributes)
    
    if cache_hit and cache_hit_counter:
        cache_hit_counter.add(1, {"model": model, "tenant_id": str(tenant_id)})
    
    if guardrail_triggered and guardrail_trigger_counter:
        guardrail_trigger_counter.add(1, {
            "tenant_id": str(tenant_id),
            "rule": guardrail_triggered
        })


def trace_llm_call(operation_name: str = "llm.request"):
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            model = kwargs.get("model", "unknown")
            attributes = {
                "llm.model": model,
                "llm.operation": operation_name,
                "llm.temperature": kwargs.get("temperature", 1.0),
                "llm.max_tokens": kwargs.get("max_tokens"),
                "llm.stream": kwargs.get("stream", False)
            }
            
            with create_span(operation_name, SpanKind.CLIENT, attributes) as span:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    
                    if isinstance(result, dict):
                        span.set_attribute("llm.provider", result.get("provider", "unknown"))
                        span.set_attribute("llm.prompt_tokens", result.get("prompt_tokens", 0))
                        span.set_attribute("llm.completion_tokens", result.get("completion_tokens", 0))
                        span.set_attribute("llm.total_tokens", result.get("total_tokens", 0))
                        span.set_attribute("llm.cost", result.get("cost", 0))
                        span.set_attribute("llm.latency_ms", result.get("latency_ms", 0))
                    
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_attribute("llm.error", str(e))
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with create_span(operation_name, SpanKind.CLIENT) as span:
                return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class TelemetryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        tracer = get_tracer()
        
        propagator = TraceContextTextMapPropagator()
        context = propagator.extract(carrier=dict(request.headers))
        
        span_name = f"{request.method} {request.url.path}"
        
        with tracer.start_as_current_span(
            span_name,
            kind=SpanKind.SERVER,
            context=context
        ) as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.host", request.url.hostname or "")
            span.set_attribute("http.target", request.url.path)
            
            if "x-api-key" in request.headers:
                span.set_attribute("api.key_present", True)
            
            start_time = time.time()
            
            try:
                response = await call_next(request)
                
                latency_ms = (time.time() - start_time) * 1000
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("http.latency_ms", latency_ms)
                
                trace_id = format(span.get_span_context().trace_id, '032x')
                span_id = format(span.get_span_context().span_id, '016x')
                
                response.headers["X-Trace-ID"] = trace_id
                response.headers["X-Span-ID"] = span_id
                
                if response.status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR))
                else:
                    span.set_status(Status(StatusCode.OK))
                
                return response
                
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise


def shutdown_telemetry():
    global _initialized
    if _initialized:
        trace_provider = trace.get_tracer_provider()
        if hasattr(trace_provider, 'force_flush'):
            trace_provider.force_flush()  # type: ignore
        
        meter_provider = metrics.get_meter_provider()
        if hasattr(meter_provider, 'force_flush'):
            meter_provider.force_flush()  # type: ignore
        
        _initialized = False
        logger.info("opentelemetry_shutdown")


def instrument_fastapi(app):
    FastAPIInstrumentor.instrument_app(app)
    logger.info("fastapi_instrumented")
