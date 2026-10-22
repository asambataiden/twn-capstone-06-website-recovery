
"""Notification contracts for website monitoring incidents."""
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    ALERT = "alert"
    RECOVERED = "recovered"


@dataclass(frozen=True, slots=True)
class Notification:
    event_type: EventType
    message: str


class Notifier(Protocol):
    """Contract implemented by notification providers."""

    def send(self, notification: Notification) -> None:
        """Deliver a notification or raise a delivery error."""
        ...


class LoggingNotifier:
    """Local notification adapter for development and testing."""

    def send(self, notification: Notification) -> None:
        logger.info(
            "NOTIFICATION: event=%s message=%s",
            notification.event_type.value,
            notification.message,
        )
