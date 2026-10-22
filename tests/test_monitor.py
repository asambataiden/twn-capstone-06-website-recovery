
"""Regression tests for website incident detection."""

import logging
from collections.abc import Iterator

from website_recovery.health import HealthCheckResult
from website_recovery.monitor import monitor_website


def test_alert_is_emitted_once_and_recovery_is_reported(caplog):
    responses: Iterator[HealthCheckResult] = iter(
        [
            HealthCheckResult(True, 200, None),
            HealthCheckResult(False, 503, None),
            HealthCheckResult(False, 503, None),
            HealthCheckResult(False, 503, None),
            HealthCheckResult(False, 503, None),
            HealthCheckResult(True, 200, None),
        ]
    )

    def fake_checker(url: str) -> HealthCheckResult:
        return next(responses)

    with caplog.at_level(logging.INFO):
        monitor_website(
            url="https://example.com",
            interval=1,
            failure_threshold=3,
            checker=fake_checker,
            sleeper=lambda seconds: None,
            max_checks=6,
        )

    messages = [record.getMessage() for record in caplog.records]

    assert sum(
        "ALERT: failure threshold reached" in message
        for message in messages
    ) == 1

    assert sum(
        "RECOVERED: website is healthy again" in message
        for message in messages
    ) == 1

    assert any(
        "consecutive_failures=3" in message
        for message in messages
    )
