
"""Regression tests for website incident detection."""

import logging
from collections.abc import Iterator

from website_recovery.health import HealthCheckResult
from website_recovery.monitor import monitor_website
from unittest.mock import Mock


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

def test_recovery_attempted_once_per_incident():
    restarter = Mock()

    responses = iter([
        HealthCheckResult(False, 503, None),
        HealthCheckResult(False, 503, None),
        HealthCheckResult(False, 503, None),
        HealthCheckResult(False, 503, None),
        HealthCheckResult(True, 200, None),
    ])

    monitor_website(
        url="https://example.com",
        interval=1,
        failure_threshold=3,
        checker=lambda url: next(responses),
        sleeper=lambda seconds: None,
        max_checks=5,
        restarter=restarter,
    )

    restarter.restart.assert_called_once()


def test_recovery_failure_does_not_stop_monitoring(caplog):

    caplog.set_level(logging.INFO, logger="website_recovery.monitor")

    restarter = Mock()
    restarter.restart.side_effect = RuntimeError(
        "Simulated Docker failure"
    )

    restarter = Mock()
    restarter.restart.side_effect = RuntimeError(
        "Simulated Docker failure"
    )

    responses = iter([
        HealthCheckResult(False, 503, None),
        HealthCheckResult(True, 200, None),
    ])

    monitor_website(
        url="https://example.com",
        interval=1,
        failure_threshold=1,
        checker=lambda url: next(responses),
        sleeper=lambda seconds: None,
        max_checks=2,
        restarter=restarter,
    )

    restarter.restart.assert_called_once()

    assert "RECOVERY FAILED" in caplog.text
    assert "RECOVERED" in caplog.text
