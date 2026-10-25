"""Opt-in Linode server reboot for the TWN cloud-recovery exercise.

This module never runs on import and does not discover or select instances.
A caller must provide the exact approved instance ID and an explicit
confirmation string. Do not invoke against shared or production servers.
"""

from dataclasses import dataclass, field
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import re


class CloudRecoveryError(RuntimeError):
    """Linode rejected or did not confirm the reboot request."""


@dataclass(frozen=True, slots=True)
class LinodeServerRebooter:
    """Reboot one explicitly authorized Linode instance via the v4 API."""

    instance_id: int
    api_token: str = field(repr=False)
    confirmation: str
    timeout: float = 10.0

    def __post_init__(self) -> None:
        if type(self.instance_id) is not int or self.instance_id < 1:
            raise ValueError("instance_id must be a positive integer")
        if not self.api_token.strip() or not re.fullmatch(
            r"[A-Za-z0-9_.-]+", self.api_token
        ):
            raise ValueError("Invalid Linode API token format")
        if self.confirmation != f"REBOOT LINODE {self.instance_id}":
            raise ValueError("Explicit Linode instance confirmation required")
        if not 0 < self.timeout < float("inf"):
            raise ValueError("timeout must be finite and positive")

    def restart(self) -> None:
        """Request an instance reboot. API acceptance is not HTTP recovery."""
        request = Request(
            url=(
                "https://api.linode.com/v4/linode/instances/"
                f"{self.instance_id}/reboot"
            ),
            data=b"{}",
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                if response.status not in (200, 202):
                    raise CloudRecoveryError(
                        "Linode did not accept the reboot request"
                    )
        except HTTPError as exc:
            raise CloudRecoveryError(
                f"Linode reboot API returned HTTP {exc.code}"
            ) from None
        except (URLError, TimeoutError, OSError):
            raise CloudRecoveryError(
                "Linode reboot API connection failed"
            ) from None


@dataclass(frozen=True, slots=True)
class DockerThenLinodeRecovery:
    """Try Docker recovery first, then one opt-in server reboot on failure."""

    docker_restarter: object
    linode_rebooter: LinodeServerRebooter

    def restart(self) -> None:
        """Escalate only if the primary adapter reports recovery action failure."""
        from website_recovery.recovery import RecoveryError

        try:
            self.docker_restarter.restart()
        except RecoveryError:
            self.linode_rebooter.restart()
