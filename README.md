# Capstone 06 — Website Monitoring and Recovery

**TechWorld with Nana · AI-Enhanced DevOps Bootcamp · DevOps Portfolio**

A Python-based website availability monitor that detects consecutive HTTP failures, raises incident alerts, optionally attempts a single controlled Docker restart per incident, and reports HTTP-verified recovery. The notification system supports a local logging adapter and Telegram Bot API messages.

> **Scope:** Educational, single-process local lab and portfolio implementation. It is **not** a production-ready high-availability controller. Docker access is privileged, monitoring state is in memory, and recovery eligibility currently relies on a configured container name. See [Security and limitations](docs/security.md).

## Capabilities

| Capability | Implementation |
| --- | --- |
| HTTP health check | `check_website()` returns immutable `HealthCheckResult` |
| Failure detection | Configurable consecutive-failure threshold |
| Incident tracking | One alert per active incident; new incident only after HTTP recovery |
| Notification abstraction | `Notifier` protocol and `LoggingNotifier` |
| Mobile notifications | `TelegramNotifier` using HTTPS POST and environment-provided credentials |
| Automatic recovery | Optional `DockerRestarter` invokes `docker container restart` |
| Failure isolation | Notification/recovery exceptions are logged without ending the monitoring loop |
| Recovery confirmation | A new successful HTTP health check is required before reporting `RECOVERED` |
| Automated checks | pytest unit tests, bytecode compilation and uv lock synchronization |

## Architecture

```text
                    HTTP GET
                        |
                        v
                 check_website()
                        |
                        v
               monitor_website()
                        |
             N consecutive failures?
                   /         \
                 no          yes (new incident)
                 |                 |
           keep checking          +------> Notifier.send(ALERT)
                                   |               |
                                   |      Logging / Telegram
                                   v
                           attempt_recovery()
                                   |
                          DockerRestarter.restart()
                          (optional, once/incident)
                                   |
                              keep checking
                                   |
                         HTTP check succeeds?
                                   |
                                  yes
                                   |
                         Notifier.send(RECOVERED)
```

Important: A Docker command reporting success does **not** prove application recovery. The monitor reports recovery only after a subsequent HTTP success.

Implementation files:

```text
src/website_recovery/
├── __init__.py
├── health.py
├── monitor.py
├── notifications.py
├── telegram.py
└── recovery.py

tests/
├── test_health.py
├── test_monitor.py
├── test_notifications.py
├── test_telegram.py
└── test_recovery.py
```

More detail: [Architecture](docs/architecture.md).

## Prerequisites

- macOS or Linux, Python **3.13**, and [uv](https://docs.astral.sh/uv/).
- Docker Engine / Docker Desktop for the optional live recovery lab.
- A Telegram bot token and a private chat ID only for real mobile notification delivery.
- A terminal with access to this repository.

The repository was developed with Python 3.13 and uses `uv.lock`. Check the project's `pyproject.toml` before changing language or dependency versions.

## Quick start

From the repository root:

```bash
uv sync --locked
PYTHONPATH=src uv run pytest -q
uv run python -m compileall -q src
```

These tests use mocked HTTP responses, notification requests and Docker execution; no Docker daemon or Telegram credentials are needed for the unit suite.

### Check a website

```bash
PYTHONPATH=src uv run python - <<'PY'
from website_recovery.health import check_website

result = check_website("https://example.com", timeout=5.0)
print(result)
PY
```

> Only monitor endpoints you own or are explicitly authorized to probe. The current health-check implementation accepts HTTP(S) URLs but does not enforce a private-network or redirect policy.

### Run the monitor with logging only

```bash
PYTHONPATH=src uv run python - <<'PY'
import logging
from website_recovery.monitor import monitor_website
from website_recovery.notifications import LoggingNotifier

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
monitor_website(
    url="https://example.com",
    interval=30.0,
    failure_threshold=3,
    max_checks=5,
    notifier=LoggingNotifier(),
)
PY
```

`max_checks` makes this example finite. The monitor has no built-in persistent state store or supervisor.

## Telegram configuration (optional)

Create a bot using Telegram's official [BotFather](https://t.me/BotFather), message the bot from your phone, and retrieve your private chat ID through the [Telegram Bot API](https://core.telegram.org/bots/api). Do not commit the token or chat ID.

In a local `zsh` terminal, enter the secret without echoing it:

```bash
read -rs "TELEGRAM_BOT_TOKEN?Bot token: "
printf '\n'
export TELEGRAM_BOT_TOKEN
read -r "TELEGRAM_CHAT_ID?Private chat ID: "
export TELEGRAM_CHAT_ID
```

Validate configuration without printing values:

```bash
PYTHONPATH=src uv run python - <<'PY'
import os
for name in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
    print(f"{name}: {'CONFIGURED' if os.getenv(name, '').strip() else 'MISSING'}")
PY
```

Send a direct test notification:

```bash
PYTHONPATH=src uv run python - <<'PY'
from website_recovery.notifications import EventType, Notification
from website_recovery.telegram import TelegramNotifier

TelegramNotifier.from_environment().send(
    Notification(EventType.ALERT, "Capstone 06 Telegram delivery test")
)
print("Telegram API accepted the message")
PY
```

Acceptance by the Telegram API does not necessarily prove the phone displayed a notification; check the actual conversation.

## Controlled Docker recovery lab

**Safety:** Only use a disposable lab container. Do not run the restarter against application, database, or production containers. Inspect existing names before creating resources. Recovery command execution uses Docker daemon access, which is highly privileged.

Follow the fully detailed, step-by-step [Deployment and recovery runbook](docs/deployment-runbook.md). It covers:

1. Validating Docker and confirming the container name is unused.
2. Creating a loopback-bound Nginx test website.
3. Stopping the test website deliberately.
4. Authorizing the test container by name, label, state and restart policy for the **lab invocation**.
5. Running the monitor with Telegram and Docker recovery enabled.
6. Confirming HTTP 200 after restart and safely cleaning up.

**Limit of authorization:** The lab runner verifies ownership before invoking the adapter, but `DockerRestarter` itself currently enforces a naming pattern rather than checking immutable container identity or labels. Do not treat the standalone adapter as a production authorization boundary.

## Testing

```bash
uv sync --locked
PYTHONPATH=src uv run pytest -v
uv run python -m compileall -q src
git diff --check
```

The project previously reported **17 passing tests** after Docker recovery integration; always use current CI/local output as the authoritative count. Unit tests use mocks and are not a substitute for the live lab.

## Verification and evidence

Document your own reproducible results in [Evidence index](evidence/README.md). Capture:

- pytest summary with all tests passing.
- Terminal showing the incident threshold, one recovery attempt and HTTP recovery event.
- A separate HTTP 200 check following Docker restart.
- Telegram alert and recovery messages, with private information redacted.
- Git commit and branch reference corresponding to the evidence.

Do not commit bot tokens, cookies, private chat identifiers, unredacted screenshots or Docker credentials.

## Operational limitations

This implementation is intentionally compact. It has no persistent incident database, leader election, distributed coordination, retry/backoff scheduler, durable notification queue or deployment controller. Recovery is synchronous; it may block a monitoring iteration until the Docker command completes or times out. Application readiness is only represented by the configured HTTP check.

See [Security and limitations](docs/security.md) for an explicit assessment and possible production hardening steps.

## Documentation

- [Architecture and incident lifecycle](docs/architecture.md)
- [Deployment, recovery and rollback runbook](docs/deployment-runbook.md)
- [Security assumptions and production gaps](docs/security.md)
- [Sanitized evidence checklist](evidence/README.md)

## Learning outcomes

This capstone demonstrates practical DevOps fundamentals: health checks, incident state, alert deduplication, fault isolation, controlled infrastructure actions, testability through dependency injection, secrets separation, verification after remediation, and operational documentation.

**Portfolio note:** This implementation is an independent learning project for the TechWorld with Nana DevOps Bootcamp. It is not represented as an official TechWorld with Nana software product.
