"""Offline tests for opt-in cloud-server reboot handling."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from website_recovery.cloud_recovery import (
    CloudRecoveryError,
    DockerThenLinodeRecovery,
    LinodeServerRebooter,
)
from website_recovery.recovery import RecoveryError


def rebooter() -> LinodeServerRebooter:
    return LinodeServerRebooter(
        instance_id=123456,
        api_token="test-token-do-not-use",
        confirmation="REBOOT LINODE 123456",
    )


@pytest.mark.parametrize("instance_id", [0, -1, "123456", True])
def test_requires_positive_numeric_instance_id(instance_id):
    with pytest.raises(ValueError):
        LinodeServerRebooter(
            instance_id=instance_id,
            api_token="test-token",
            confirmation=f"REBOOT LINODE {instance_id}",
        )


def test_rejects_missing_confirmation():
    with pytest.raises(ValueError, match="confirmation"):
        LinodeServerRebooter(123456, "test-token", "")


def test_rejects_empty_api_token():
    with pytest.raises(ValueError, match="token"):
        LinodeServerRebooter(123456, "", "REBOOT LINODE 123456")


def test_api_request_is_scoped_and_uses_post():
    response = MagicMock()
    response.status = 200
    response.__enter__.return_value = response

    with patch("website_recovery.cloud_recovery.urlopen", return_value=response) as opener:
        rebooter().restart()

    request = opener.call_args.args[0]
    assert request.full_url == "https://api.linode.com/v4/linode/instances/123456/reboot"
    assert request.get_method() == "POST"
    assert opener.call_args.kwargs["timeout"] == 10.0
    assert request.data == b"{}"


def test_cloud_failure_does_not_leak_token():
    from urllib.error import HTTPError

    error = HTTPError(
        "https://api.linode.com/v4/linode/instances/123456/reboot",
        403,
        "Forbidden",
        None,
        None,
    )
    with patch("website_recovery.cloud_recovery.urlopen", side_effect=error):
        with pytest.raises(CloudRecoveryError, match="HTTP 403") as exc:
            rebooter().restart()

    assert "test-token" not in str(exc.value)


def test_fallback_does_not_run_when_docker_restart_succeeds():
    docker = Mock()
    cloud = Mock()
    plan = DockerThenLinodeRecovery(docker, cloud)
    plan.restart()

    docker.restart.assert_called_once_with()
    cloud.restart.assert_not_called()


def test_fallback_runs_once_on_docker_recovery_error():
    docker = Mock()
    docker.restart.side_effect = RecoveryError("Docker command failed")
    cloud = Mock()

    DockerThenLinodeRecovery(docker, cloud).restart()

    docker.restart.assert_called_once_with()
    cloud.restart.assert_called_once_with()


def test_unknown_exception_does_not_reboot_cloud():
    docker = Mock()
    docker.restart.side_effect = ValueError("unexpected input")
    cloud = Mock()
    with pytest.raises(ValueError):
        DockerThenLinodeRecovery(docker, cloud).restart()
    cloud.restart.assert_not_called()
