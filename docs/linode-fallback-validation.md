# Capstone 06 — Verify automatic fallback to a real Linode VM reboot

## Why this test

We previously verified (1) a **real** outage and automatic **SSH Docker** recovery with mobile alerts and (2) a separately **operator-triggered** Linode API VM reboot that restored Nginx. The remaining code path is `DockerThenLinodeRecovery`: an error from the primary Docker recovery must **automatically** call the configured Linode server rebooter.

This lab verifies that path without deliberately breaking SSH credentials or Docker access.

**Precise evidence boundary:** The primary Docker failure is **injected by a simulator** that raises `RecoveryError`. The fallback uses the **real** Linode API and reboots the **real** dedicated VM after the operator explicitly authorizes it. Thus this proves automatic **code-path escalation and real VM recovery**, not detection of a naturally occurring SSH failure or unattended operation without prior approval.

## Preconditions

- Only the dedicated disposable Linode `twn-capstone06-webserver` (ID `109140229`, `eu-central`, IPv4 `172.104.229.93`) is authorized.
- On Linode, `docker inspect twn-recovery-website` reports `running` and `unless-stopped`; the website returns HTTP 200 from Mac before testing.
- Verify no unrelated workloads are running and the Linode console is accessible.
- Keep your already-tested Telegram bot token and chat ID in your local shell environment, not source control.
- Linode token with sufficient permissions is entered securely at the prompt; no credentials in commands, Git or screenshots.
- The VM reboot causes real temporary website downtime and disrupts SSH connections. This is a **single-shot** test, not a scheduled monitor/reboot loop.

## 1. Validate first (Mac terminal)

```bash
git fetch origin
git switch --track origin/feat/cap06-verify-live-vm-fallback
uv sync --locked
uv run pytest -q
PYTHONPATH=src uv run python scripts/verify-linode-fallback.py
```

Without `--execute`, the verification script only prints its configured target and intent. **No network or reboot operation takes place.**

## 2. Start independent website monitor (Mac Terminal A)

```bash
PYTHONPATH=src uv run python -u - <<'PY'
import logging
from website_recovery.monitor import monitor_website
from website_recovery.telegram import TelegramNotifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", force=True)
print("Watching real Linode availability through fallback reboot...", flush=True)
monitor_website(
    url="http://172.104.229.93/",
    interval=2.0,
    failure_threshold=2,
    max_checks=300,
    notifier=TelegramNotifier.from_environment(),
    restarter=None,
)
print("Monitoring completed.", flush=True)
PY
```

Monitoring is deliberately observation-only: **do not attach an additional rebooter**. A fast reboot might not cross the failure threshold, so Telegram ALERT/RECOVERED are conditional on actual observations.

## 3. Execute one controlled fallback (Mac Terminal B)

```bash
PYTHONPATH=src uv run python scripts/verify-linode-fallback.py --execute
```

The script verifies baseline HTTP 200, reads Linode instance identity from the API, requires an exact confirmation and then executes:

```text
SimulatedFailedDockerRestarter.restart()
    -> raises RecoveryError
DockerThenLinodeRecovery.restart()
    -> LinodeServerRebooter.restart()
    -> POST reboot of the single verified VM
```

Type `REBOOT LINODE 109140229` only if the target details are correct and this temporary downtime is authorized.

## 4. Verify independently after Linode is reachable again

On Linode:

```bash
uptime -s
systemctl is-active docker
docker inspect twn-recovery-website \
  --format 'State={{.State.Status}} Policy={{.HostConfig.RestartPolicy.Name}}'
curl --fail --silent --show-error --max-time 5 \
  -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1/
```

On Mac:

```bash
curl -4 --noproxy '*' --fail --silent --show-error --max-time 10 \
  -o /dev/null -w 'HTTP %{http_code}\n' http://172.104.229.93/
```

Compare the post-reboot `uptime -s` against the previously observed `2026-10-25 05:42:59`. Keep sanitized timestamps and optionally screenshots of Telegram messages if the outage was observed.

## Acceptance evidence

- `[LAB] Injected Docker RecoveryError (simulation).` appears.
- `SUCCESS: fallback issued Linode API reboot request.` appears.
- Linode `uptime -s` changes after the request.
- Docker is active, Nginx container returns to running, and local plus external HTTP checks return 200.
- The monitor's actual incident logs and Telegram messages are recorded only if they actually occurred.

**Do not call this a genuine Docker or SSH infrastructure failure test.** The injected failure demonstrates the fallback branch; the VM reboot and post-boot HTTP checks demonstrate the real cloud effect. Keep the original real Docker outage evidence separate.
