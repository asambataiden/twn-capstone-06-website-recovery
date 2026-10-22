
"""Telegram notification adapter for website monitoring."""

import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from website_recovery.notifications import Notification


class NotificationDeliveryError(RuntimeError):
    """Raised when a notification cannot be delivered."""


@dataclass(frozen=True, slots=True)
class TelegramNotifier:
    """Send incident notifications using the Telegram Bot API."""

    token: str
    chat_id: str
    timeout: float = 10.0

    def __post_init__(self) -> None:
        if not self.token.strip() or not self.chat_id.strip():
            raise ValueError("Telegram credentials must be configured")

        if not 0 < self.timeout < float("inf"):
            raise ValueError("Timeout must be a finite positive number")

    @classmethod
    def from_environment(cls) -> "TelegramNotifier":
        """Read credentials from process environment variables."""
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

        return cls(token=token, chat_id=chat_id)

    def send(self, notification: Notification) -> None:
        """Send a Telegram text message or raise a sanitized error."""
        message = (
            f"[TWN WEBSITE MONITOR]\n"
            f"Event: {notification.event_type.value.upper()}\n"
            f"{notification.message}"
        )

        payload = json.dumps(
            {
                "chat_id": self.chat_id,
                "text": message,
            }
        ).encode("utf-8")

        request = Request(
            url=f"https://api.telegram.org/bot{self.token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.load(response)

            if result.get("ok") is not True:
                raise NotificationDeliveryError(
                    "Telegram rejected the notification"
                )

        except HTTPError as exc:
            # Never print exc or its URL: the URL includes the bot token.
            raise NotificationDeliveryError(
                f"Telegram returned HTTP {exc.code}"
            ) from None

        except (URLError, TimeoutError, OSError):
            raise NotificationDeliveryError(
                "Telegram connection or timeout failure"
            ) from None

        except (ValueError, UnicodeError):
            raise NotificationDeliveryError(
                "Invalid Telegram API response"
            ) from None
