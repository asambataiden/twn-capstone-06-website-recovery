from dataclasses import FrozenInstanceError
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pytest

from website_recovery.health import HealthCheckResult, check_website


def test_healthy_http_response():
    response = BytesIO(b"OK")
    response.status = 200

    with patch(
            "website_recovery.health.urlopen",
            return_value=response,
    ):
        result = check_website("https://example.com")

    assert result == HealthCheckResult(
        healthy=True,
        status_code=200,
        error=None,
    )


def test_unhealthy_http_response():
    error = HTTPError(
        url="https://example.com",
        code=503,
        msg="Service Unavailable",
        hdrs=None,
        fp=None,
    )

    with patch(
            "website_recovery.health.urlopen",
            side_effect=error,
    ):
        result = check_website("https://example.com")

    assert result == HealthCheckResult(
        healthy=False,
        status_code=503,
        error=None,
    )


def test_connection_failure():
    with patch(
            "website_recovery.health.urlopen",
            side_effect=URLError("Connection refused"),
    ):
        result = check_website("https://example.com")

    assert result.healthy is False
    assert result.status_code is None
    assert result.error == "URLError"


def test_timeout():
    with patch(
            "website_recovery.health.urlopen",
            side_effect=TimeoutError("Timed out"),
    ):
        result = check_website("https://example.com")

    assert result.healthy is False
    assert result.status_code is None
    assert result.error == "TimeoutError"


def test_rejects_invalid_url_scheme():
    with pytest.raises(ValueError, match="HTTP or HTTPS"):
        check_website("ftp://example.com")


def test_rejects_invalid_timeout():
    with pytest.raises(ValueError, match="Timeout must be positive"):
        check_website("https://example.com", timeout=0)


def test_health_result_is_immutable():
    result = HealthCheckResult(
        healthy=True,
        status_code=200,
        error=None,
    )

    with pytest.raises(FrozenInstanceError):
        result.healthy = False