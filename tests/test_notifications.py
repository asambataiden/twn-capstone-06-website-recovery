
"""Tests for notification integration and failure isolation."""

import logging
from unittest.mock import Mock

from website_recovery.health import HealthCheckResult
from website_recovery.monitor import monitor_website
from website_recovery.notifications import EventType


def test_alert_and_recovery_notifications():
    notifier = Mock()
    responses = iter([
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
        max_checks=4,
        notifier=notifier,
    )

    assert notifier.send.call_count == 2

    events = [
        call.args[0].event_type
        for call in notifier.send.call_args_list
    ]

    assert events == [
        EventType.ALERT,
        EventType.RECOVERED,
    ]


def test_notification_failure_does_not_stop_monitoring(caplog):
    notifier = Mock()
    notifier.send.side_effect = RuntimeError("Provider unavailable")

    responses = iter([
        HealthCheckResult(False, 503, None),
        HealthCheckResult(True, 200, None),
    ])

    with caplog.at_level(logging.ERROR):
        monitor_website(
            url="https://example.com",
            interval=1,
            failure_threshold=1,
            checker=lambda url: next(responses),
            sleeper=lambda seconds: None,
            max_checks=2,
            notifier=notifier,
        )

    assert notifier.send.call_count == 2
    assert "Notification delivery failed" in caplog.text
