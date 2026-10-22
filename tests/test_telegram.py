
"""Tests for the Telegram notification adapter."""

import json
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from website_recovery.notifications import EventType, Notification
from website_recovery.telegram import (
    NotificationDeliveryError,
    TelegramNotifier,
)


def test_sends_notification_using_https_post():
    notifier = TelegramNotifier(
        token="test-token",
        chat_id="123456",
    )
    notification = Notification(
        event_type=EventType.ALERT,
        message="Website unavailable",
    )

    response = BytesIO(b'{"ok": true, "result": {"message_id": 1}}')

    with patch(
            "website_recovery.telegram.urlopen",
            return_value=response,
    ) as mock_urlopen:
        notifier.send(notification)

    request = mock_urlopen.call_args.args[0]
    payload = json.loads(request.data)

    assert request.full_url.startswith("https://api.telegram.org/")
    assert request.get_method() == "POST"
    assert payload["chat_id"] == "123456"
    assert "Website unavailable" in payload["text"]


def test_http_failure_does_not_expose_token():
    notifier = TelegramNotifier(
        token="sensitive-test-token",
        chat_id="123456",
    )

    http_error = HTTPError(
        url="https://api.telegram.org/botsensitive-test-token/sendMessage",
        code=401,
        msg="Unauthorized",
        hdrs=None,
        fp=None,
    )

    with patch(
            "website_recovery.telegram.urlopen",
            side_effect=http_error,
    ):
        with pytest.raises(
                NotificationDeliveryError,
                match="Telegram returned HTTP 401",
        ) as exc_info:
            notifier.send(
                Notification(
                    event_type=EventType.ALERT,
                    message="Website unavailable",
                )
            )

    assert "sensitive-test-token" not in str(exc_info.value)
