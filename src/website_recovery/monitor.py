
"""Periodic website health monitoring and incident detection."""

import logging
import time
from collections.abc import Callable

from website_recovery.health import HealthCheckResult, check_website
from website_recovery.notifications import Notification, EventType, Notifier

logger = logging.getLogger(__name__)

HealthChecker = Callable[[str], HealthCheckResult]
Sleeper = Callable[[float], None]


def send_notification(
        notifier: Notifier | None,
        notification: Notification,
) -> None:
    """Attempt notification delivery without stopping monitoring."""
    if notifier is None:
        return

    try:
        notifier.send(notification)
    except Exception:
        logger.exception(
            "Notification delivery failed for event=%s",
            notification.event_type.value,
        )

def monitor_website(
        url: str,
        interval: float = 30.0,
        failure_threshold: int = 3,
        *,
        checker: HealthChecker | None = None,
        sleeper: Sleeper = time.sleep,
        max_checks: int | None = None,
        notifier: Notifier | None = None,
) -> None:
    """Monitor a website and report incident state transitions.

    A threshold breach emits one incident alert. After the
    website recovers, a later failure can trigger a new alert.

    Args:
        url: Trusted HTTP(S) endpoint to monitor.
        interval: Delay between completed checks, in seconds.
        failure_threshold: Consecutive failures before alerting.
        checker: Optional health-check implementation for testing.
        sleeper: Optional sleep implementation for testing.
        max_checks: Optional number of checks before stopping.
    """
    if not 0 < interval < float("inf"):
        raise ValueError("interval must be a finite positive number")

    if type(failure_threshold) is not int or failure_threshold < 1:
        raise ValueError("failure_threshold must be a positive integer")

    if max_checks is not None and (
            type(max_checks) is not int or max_checks < 1
    ):
        raise ValueError("max_checks must be a positive integer")

    health_checker = checker if checker is not None else check_website

    consecutive_failures = 0
    incident_active = False
    checks_completed = 0

    while max_checks is None or checks_completed < max_checks:
        result = health_checker(url)
        checks_completed += 1

        if result.healthy:
            consecutive_failures = 0

            if incident_active:
                logger.info("RECOVERED: website is healthy again")
                incident_active = False

                send_notification(
                    notifier,
                    Notification(
                        event_type=EventType.RECOVERED,
                        message=f"Website {url} is healthy again.",
                    ),
                )

        else:
            consecutive_failures += 1

            logger.warning(
                "UNHEALTHY: status_code=%s error=%s "
                "consecutive_failures=%d",
                result.status_code,
                result.error,
                consecutive_failures,
            )

            if (
                    consecutive_failures >= failure_threshold
                    and not incident_active
            ):
                incident_active = True

                logger.error(
                    "ALERT: failure threshold reached (%d)",
                    failure_threshold,
                )

                send_notification(
                    notifier,
                    Notification(
                        event_type=EventType.ALERT,
                        message=(
                            f"Website {url} failed "
                            f"{consecutive_failures} consecutive checks."
                        ),
                    ),
                )

        if max_checks is None or checks_completed < max_checks:
            sleeper(interval)
