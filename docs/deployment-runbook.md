# Deployment and Recovery Runbook — Local Docker Lab

## 1. Scope and authorization

Run only on a local development host with Docker Engine/Docker Desktop. This runbook controls a **disposable Nginx container** named `twn-recovery-website` published on `127.0.0.1:18080`. Do not reuse the name for a production workload. Docker access is privileged; use a trusted local user session.

## 2. Prerequisites and baseline checks

```bash
uv sync --locked
PYTHONPATH=src uv run pytest -q
docker version
docker info --format '{{.ServerVersion}}'
docker context show
```

Check that both the container name and chosen port are available. **Stop if an unrelated container already uses this name.**

```bash
docker container inspect twn-recovery-website --format '{{.Name}}' 2>/dev/null || true
```

If an existing object is found, inspect it and use a clean dedicated Docker environment rather than deleting it blindly. Check port availability using `lsof -nP -iTCP:18080 -sTCP:LISTEN` on macOS, if available.

## 3. Create the disposable website

```bash
docker run -d \
  --name twn-recovery-website \
  --label dev.twn.capstone=06 \
  --restart=no \
  -p 127.0.0.1:18080:80 \
  nginx:alpine
```

For a stronger reproducibility/security baseline, replace the floating `nginx:alpine` tag with an explicitly reviewed image digest and record it as deployment evidence. This tutorial uses the simple tag for ease of learning.

```bash
docker inspect twn-recovery-website \
  --format 'Name={{.Name}} State={{.State.Status}} Policy={{.HostConfig.RestartPolicy.Name}} Label={{index .Config.Labels "dev.twn.capstone"}}'

curl --noproxy '*' -sS -o /dev/null -w 'HTTP %{http_code}\n' \
  --max-time 5 http://127.0.0.1:18080/
```

Expected when ready: `State=running`, `Policy=no`, `Label=06`, `HTTP 200`.

## 4. Configure notifications (optional)

Use the BotFather-issued bot token and the private conversation chat ID. Never put them in tracked files or shell command arguments. In `zsh`:

```bash
read -rs "TELEGRAM_BOT_TOKEN?Bot token: "
printf '\n'
export TELEGRAM_BOT_TOKEN
read -r "TELEGRAM_CHAT_ID?Private chat ID: "
export TELEGRAM_CHAT_ID
```

For a test without Telegram, remove `notifier=TelegramNotifier.from_environment()` from the Python invocation below, or replace it with `LoggingNotifier()` and update the imports.

## 5. Inject the failure

This command touches **only** the lab container:

```bash
docker stop twn-recovery-website
docker inspect twn-recovery-website --format '{{.State.Status}}'
```

Expected state: `exited`.

## 6. Start bounded incident monitoring and recovery

The following lab invocation checks the intended resource's name, label, restart policy and state immediately before startup. These checks are a **lab safeguard**, not a security guarantee against changes between validation and use.

```bash
PYTHONPATH=src uv run python - <<'PY'
import logging
import subprocess

from website_recovery.monitor import monitor_website
from website_recovery.recovery import DockerRestarter
from website_recovery.telegram import TelegramNotifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

container = "twn-recovery-website"
expected = {
    "{{.Name}}": "/twn-recovery-website",
    "{{index .Config.Labels \"dev.twn.capstone\"}}": "06",
    "{{.HostConfig.RestartPolicy.Name}}": "no",
    "{{.State.Status}}": "exited",
}

for template, required in expected.items():
    result = subprocess.run(
        ["docker", "inspect", "--format", template, container],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    if result.stdout.strip() != required:
        raise RuntimeError("Lab container authorization check failed")

monitor_website(
    url="http://127.0.0.1:18080/",
    interval=2.0,
    failure_threshold=3,
    max_checks=12,
    notifier=TelegramNotifier.from_environment(),
    restarter=DockerRestarter(
        container_name=container,
        command_timeout=20.0,
        stop_timeout=5,
    ),
)
PY
```

Expected event sequence: 3 unhealthy checks -> 1 ALERT -> 1 Docker restart attempt -> HTTP success -> RECOVERED. Startup timing may differ; evaluate actual logs and the final probe. The script performs a bounded number of checks, not a bounded total wall-clock runtime.

## 7. Verify recovery independently

```bash
docker inspect twn-recovery-website \
  --format 'State={{.State.Status}} StartedAt={{.State.StartedAt}}'

curl --noproxy '*' -sS -o /dev/null -w 'HTTP %{http_code}\n' \
  --max-time 5 http://127.0.0.1:18080/
```

Only record a successful application recovery when the HTTP endpoint returns 200. Also confirm alert/recovered Telegram messages if notifications are enabled.

## 8. Troubleshooting

| Symptom | Checks |
| --- | --- |
| `docker: command not found` | Install Docker CLI / verify PATH |
| Cannot connect to Docker daemon | Start Docker Desktop, check active context |
| Port 18080 already in use | Stop/relocate conflicting **lab** service; do not interrupt unrelated workloads |
| Container remains exited | `docker logs twn-recovery-website`; inspect Docker state and restart errors |
| Restart succeeds but HTTP fails | Inspect Nginx logs, port mapping and application startup readiness |
| Telegram HTTP 401 | Verify active BotFather token without printing it |
| Telegram credentials missing | Export both environment variables in the same shell |
| No `RECOVERED` event | Check subsequent HTTP status; restart action alone does not signify recovery |

Do not paste token-bearing exception URLs into issues, support tickets or project evidence.

## 9. Rollback / cleanup

First confirm this is our labelled lab container:

```bash
docker inspect twn-recovery-website \
  --format 'Name={{.Name}} Label={{index .Config.Labels "dev.twn.capstone"}}'
```

Only if name and label match the lab resource:

```bash
docker rm -f twn-recovery-website
```

The image remains cached. Do not run broad prune commands as part of this lab. To end the current shell's credential exposure:

```bash
unset TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID
```

## 10. Evidence

See [`../evidence/README.md`](../evidence/README.md) for redaction, filenames and required proof. Preserve sanitized logs and screenshots before removing lab resources.
