
"""Tests for controlled Docker recovery."""

import subprocess
from unittest.mock import patch

import pytest

from website_recovery.recovery import DockerRestarter, RecoveryError


def test_restart_uses_explicit_container():
    restarter = DockerRestarter("twn-recovery-website")

    with patch("website_recovery.recovery.subprocess.run") as run:
        restarter.restart()

    args, kwargs = run.call_args

    assert args[0] == [
        "docker",
        "container",
        "restart",
        "--timeout",
        "5",
        "twn-recovery-website",
    ]
    assert kwargs["check"] is True
    assert kwargs["timeout"] == 20.0


def test_rejects_unapproved_container_name():
    with pytest.raises(ValueError):
        DockerRestarter("production-database")


def test_docker_failure_is_sanitized():
    restarter = DockerRestarter("twn-recovery-website")

    error = subprocess.CalledProcessError(
        returncode=1,
        cmd=["docker", "container", "restart"],
        stderr="Potentially sensitive Docker diagnostics",
    )

    with patch(
            "website_recovery.recovery.subprocess.run",
            side_effect=error,
    ):
        with pytest.raises(
                RecoveryError,
                match="Docker rejected the container restart",
        ) as exc_info:
            restarter.restart()

    assert "sensitive" not in str(exc_info.value)
