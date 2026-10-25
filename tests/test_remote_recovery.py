"""Offline tests for SSH-only remote Docker recovery."""
from pathlib import Path
from unittest.mock import patch
import subprocess
import pytest

from website_recovery.recovery import RecoveryError
from website_recovery.remote_recovery import SSHRemoteDockerRestarter


def restarter(tmp_path: Path):
    identity = tmp_path / "lab-key"
    known_hosts = tmp_path / "known_hosts"
    identity.write_text("mock", encoding="utf-8")
    known_hosts.write_text("mock", encoding="utf-8")
    return SSHRemoteDockerRestarter(
        host="192.0.2.10", identity_file=identity, known_hosts_file=known_hosts
    )


def test_ssh_uses_known_hosts_and_fixed_remote_command(tmp_path):
    recovery = restarter(tmp_path)
    with patch("website_recovery.remote_recovery.subprocess.run") as run:
        recovery.restart()
    cmd = run.call_args.args[0]
    assert cmd[0] == "ssh"
    assert "StrictHostKeyChecking=yes" in cmd
    assert "BatchMode=yes" in cmd
    assert "IdentitiesOnly=yes" in cmd
    assert f"UserKnownHostsFile={tmp_path / 'known_hosts'}" in cmd
    assert cmd[-2:] == ["root@192.0.2.10", "bash /root/cap06-recover-website.sh"]
    assert run.call_args.kwargs["check"] is True
    assert run.call_args.kwargs["timeout"] == 30.0


@pytest.mark.parametrize("host", ["example.com", "127.0.0.1;touch /tmp/unsafe", "::1", ""])
def test_rejects_non_ipv4_or_unsafe_host(tmp_path, host):
    with pytest.raises(ValueError, match="IPv4"):
        SSHRemoteDockerRestarter(
            host=host,
            identity_file=tmp_path / "missing",
            known_hosts_file=tmp_path / "missing",
        )


def test_fails_closed_when_known_hosts_missing(tmp_path):
    key = tmp_path / "key"
    key.write_text("dummy", encoding="utf-8")
    with pytest.raises(ValueError, match="known_hosts"):
        SSHRemoteDockerRestarter("192.0.2.10", key, tmp_path / "missing")


def test_ssh_failure_sanitized(tmp_path):
    recovery = restarter(tmp_path)
    with patch(
        "website_recovery.remote_recovery.subprocess.run",
        side_effect=subprocess.CalledProcessError(255, ["ssh"], stderr="sensitive detail"),
    ):
        with pytest.raises(RecoveryError, match="Remote Capstone 06") as caught:
            recovery.restart()
    assert "sensitive detail" not in str(caught.value)
