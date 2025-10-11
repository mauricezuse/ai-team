from typing import Optional

_tracer = None

def init_otel(service_name: str = "ai-team-backend"):
    global _tracer
    try:
        from opentelemetry import trace  # type: ignore
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter  # type: ignore
        provider = TracerProvider()
        processor = BatchSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(service_name)
    except Exception:
        _tracer = None

def get_tracer():
    return _tracer

class maybe_span:
    def __init__(self, name: str):
        self.name = name
        self._span = None

    def __enter__(self):
        tracer = get_tracer()
        if tracer is not None:
            self._span = tracer.start_as_current_span(self.name)
            return self._span.__enter__()
        return None

    def __exit__(self, exc_type, exc, tb):
        if self._span is not None:
            return self._span.__exit__(exc_type, exc, tb)
        return False

