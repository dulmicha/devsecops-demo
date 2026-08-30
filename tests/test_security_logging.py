import asyncio
import io
import json
import logging
from unittest.mock import AsyncMock

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from app.core.logging import CorrelationIdFilter, request_id_ctx, setup_logging
from app.core.middleware import RequestLoggingMiddleware


def test_generated_correlation_id(client: TestClient) -> None:
    """Verify that an X-Request-ID header is automatically generated if omitted."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    request_id = response.headers["X-Request-ID"]
    assert len(request_id) > 10  # Valid UUID string


def test_propagated_correlation_id(client: TestClient) -> None:
    """Verify that a client-supplied X-Request-ID header is preserved."""
    custom_id = "trace-custom-secops-9876"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id


def test_correlation_id_filter() -> None:
    """Verify CorrelationIdFilter attaches the current context variable value."""
    token = request_id_ctx.set("unit-test-id-1122")
    try:
        log_filter = CorrelationIdFilter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        assert log_filter.filter(record) is True
        assert getattr(record, "request_id", None) == "unit-test-id-1122"
    finally:
        request_id_ctx.reset(token)


def test_structured_json_formatter() -> None:
    """Verify that setup_logging configures JsonFormatter emitting valid structured JSON."""
    setup_logging(log_level="DEBUG")
    stream = io.StringIO()
    test_handler = logging.StreamHandler(stream)

    # Use formatter from root logger
    root = logging.getLogger()
    if root.handlers:
        test_handler.setFormatter(root.handlers[0].formatter)
        test_handler.addFilter(CorrelationIdFilter())

    test_logger = logging.getLogger("app.test")
    test_logger.addHandler(test_handler)
    try:
        token = request_id_ctx.set("formatter-test-id")
        test_logger.info("Structured logging test message", extra={"custom_metric": 42})
        request_id_ctx.reset(token)

        output = stream.getvalue().strip()
        assert output.startswith("{")
        parsed = json.loads(output)
        assert parsed["logger"] == "app.test"
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Structured logging test message"
        assert parsed["request_id"] == "formatter-test-id"
        assert parsed["custom_metric"] == 42
        assert "timestamp" in parsed
    finally:
        test_logger.removeHandler(test_handler)


def test_middleware_exception_logging() -> None:
    """Verify middleware error logging when an unhandled exception occurs."""
    middleware = RequestLoggingMiddleware(app=None)
    mock_request = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/failing-route",
            "headers": [(b"host", b"testserver")],
            "client": ("127.0.0.1", 12345),
        }
    )

    failing_call_next = AsyncMock(side_effect=RuntimeError("Simulated internal crash"))

    with pytest.raises(RuntimeError, match="Simulated internal crash"):
        asyncio.run(middleware.dispatch(mock_request, failing_call_next))
