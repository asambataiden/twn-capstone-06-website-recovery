from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True, slots=True)
class HealthCheckResult:
    healthy: bool
    status_code: int | None
    error: str | None


def check_website(url: str, timeout: float = 5.0) -> HealthCheckResult:
    """Check a website's HTTP availability."""
    if not url.startswith(("http://", "https://")):
        raise ValueError("URL must use HTTP or HTTPS.")

    if timeout <= 0:
        raise ValueError("Timeout must be positive.")

    request = Request(url, method="GET")

    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
            return HealthCheckResult(
                healthy=status == 200,
                status_code=status,
                error=None,
            )

    except HTTPError as exc:
        return HealthCheckResult(
            healthy=False,
            status_code=exc.code,
            error=None,
        )

    except (URLError, TimeoutError, OSError) as exc:
        return HealthCheckResult(
            healthy=False,
            status_code=None,
            error=type(exc).__name__,
        )