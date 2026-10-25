"""Remote recovery of the dedicated Capstone 06 Linode website via verified SSH."""
from dataclasses import dataclass
from pathlib import Path
import ipaddress
import subprocess

from website_recovery.recovery import RecoveryError


@dataclass(frozen=True, slots=True)
class SSHRemoteDockerRestarter:
    """Invoke a fixed remote lab recovery script over pinned-host-key SSH.

    This adapter does not provision keys, edit known_hosts, or trust unknown hosts.
    The remote script checks Compose ownership before touching any container.
    """

    host: str
    identity_file: Path
    known_hosts_file: Path
    username: str = "root"
    timeout: float = 30.0

    def __post_init__(self) -> None:
        try:
            ipaddress.IPv4Address(self.host)
        except ipaddress.AddressValueError:
            raise ValueError("host must be an explicit IPv4 address") from None
        if self.username != "root":
            raise ValueError("This lab adapter currently supports the root lab account only")
        if not 0 < self.timeout < float("inf"):
            raise ValueError("SSH timeout must be finite and positive")
        if not self.identity_file.expanduser().is_file():
            raise ValueError("SSH identity file was not found")
        if not self.known_hosts_file.expanduser().is_file():
            raise ValueError("SSH known_hosts file was not found")

    def restart(self) -> None:
        command = [
            "ssh",
            "-o", "BatchMode=yes",
            "-o", "IdentitiesOnly=yes",
            "-o", "StrictHostKeyChecking=yes",
            "-o", f"UserKnownHostsFile={self.known_hosts_file.expanduser()}",
            "-o", "ConnectTimeout=8",
            "-i", str(self.identity_file.expanduser()),
            f"{self.username}@{self.host}",
            "bash /root/cap06-recover-website.sh",
        ]
        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            # No raw SSH output or user-specific paths in incident logs.
            raise RecoveryError("Remote Capstone 06 Docker recovery failed") from None
