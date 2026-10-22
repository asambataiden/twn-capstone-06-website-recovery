
"""Controlled Docker container recovery."""

import re
import subprocess
from dataclasses import dataclass


class RecoveryError(RuntimeError):
    """Raised when a recovery operation fails."""


@dataclass(frozen=True, slots=True)
class DockerRestarter:
    """Restart one explicitly designated Docker container."""

    container_name: str
    command_timeout: float = 20.0
    stop_timeout: int = 5

    def __post_init__(self) -> None:
        # Require the dedicated capstone container naming convention.
        if not re.fullmatch(
                r"twn-recovery-[a-zA-Z0-9][a-zA-Z0-9_.-]*",
                self.container_name,
        ):
            raise ValueError(
                "Container name must start with 'twn-recovery-'"
            )

        if not 0 < self.command_timeout < float("inf"):
            raise ValueError(
                "Command timeout must be a finite positive number"
            )

        if type(self.stop_timeout) is not int or not 1 <= self.stop_timeout <= 10:
            raise ValueError(
                "Stop timeout must be an integer from 1 to 10"
            )

    def restart(self) -> None:
        """Restart the configured container or raise a recovery error."""
        command = [
            "docker",
            "container",
            "restart",
            "--timeout",
            str(self.stop_timeout),
            self.container_name,
        ]

        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=self.command_timeout,
            )
        except subprocess.TimeoutExpired:
            raise RecoveryError(
                "Docker restart command timed out"
            ) from None
        except subprocess.CalledProcessError:
            raise RecoveryError(
                "Docker rejected the container restart"
            ) from None
        except OSError:
            raise RecoveryError(
                "Docker CLI could not be executed"
            ) from None
