# Live Linode Docker recovery — TWN Capstone 06

This is the **cloud-hosted** counterpart to the existing local-only recovery lab.
It reuses `monitor_website`, `TelegramNotifier`, and the dedicated Compose
container `twn-recovery-website`.

## Safety prerequisites

- Lab server is dedicated and disposable; restrict SSH to your trusted IP in the Linode Cloud Firewall.
- The host's SSH fingerprint was authenticated when first connected. **Do not** use `StrictHostKeyChecking=no` or blindly trust `ssh-keyscan`.
- The monitor runs on your Mac; it has an approved private SSH key and a verified `~/.ssh/known_hosts` entry.
- Remote execution uses the **root lab account** and has broad host privileges; this approach is a **bootcamp demo, not production least-privilege design**.
- This workflow never calls the Linode API server reboot adapter. Treat server reboot as a separate, explicitly approved exercise.

## 1. On Mac: synchronize the feature branch

```bash
git fetch origin
git switch --track origin/feat/cap06-ssh-remote-docker-recovery
uv sync --locked
uv run pytest -q
bash -n deploy/linode/cap06-recover-website.sh
```

## 2. Transfer the server-side recovery guard

```bash
scp -o IdentitiesOnly=yes -i ~/.ssh/id_ed25519_github_asambataiden \
  deploy/linode/cap06-recover-website.sh \
  root@172.104.229.93:/root/cap06-recover-website.sh
```

On Linode, validate it **without running the recovery operation**:

```bash
bash -n /root/cap06-recover-website.sh
chmod 700 /root/cap06-recover-website.sh
docker inspect twn-recovery-website \
  --format 'Name={{.Name}} Project={{index .Config.Labels "com.docker.compose.project"}} Capstone={{index .Config.Labels "dev.twn.capstone"}}'
```

Expect: `/twn-recovery-website`, project `twn-capstone06`, capstone `06`.

## 3. From Mac: verify remote SSH and HTTPS notifications

```bash
ssh -o BatchMode=yes -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=yes \
  -i ~/.ssh/id_ed25519_github_asambataiden \
  root@172.104.229.93 'test -f /root/cap06-recover-website.sh && echo "Remote recovery script present"'
```

Ensure the already-tested `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` variables exist in this terminal. Never echo or commit credentials.

## 4. Controlled outage (only after steps 1–3 succeed)

Run the monitor on your **Mac** in Terminal A:

```bash
PYTHONPATH=src uv run python - <<'PY'
import logging
from pathlib import Path
from website_recovery.monitor import monitor_website
from website_recovery.remote_recovery import SSHRemoteDockerRestarter
from website_recovery.telegram import TelegramNotifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

monitor_website(
    url="http://172.104.229.93/",
    interval=2.0,
    failure_threshold=3,
    max_checks=30,
    notifier=TelegramNotifier.from_environment(),
    restarter=SSHRemoteDockerRestarter(
        host="172.104.229.93",
        identity_file=Path.home() / ".ssh/id_ed25519_github_asambataiden",
        known_hosts_file=Path.home() / ".ssh/known_hosts",
    ),
)
PY
```

Once the monitor is running, **in a separate SSH terminal**, stop only
the verified lab container on Linode:

```bash
docker inspect twn-recovery-website \
  --format 'Name={{.Name}} Project={{index .Config.Labels "com.docker.compose.project"}} Capstone={{index .Config.Labels "dev.twn.capstone"}}'
docker stop twn-recovery-website
```

Expect 3 failed checks, one phone `ALERT`, remote restart, HTTP 200,
then a `RECOVERED` notification on your phone. Record actual behavior;
these results have **not yet been demonstrated** for this remote workflow.
The controller permits one restart attempt per incident while running.
No server reboot is performed.

## 5. Independent verification

From Mac:

```bash
curl --fail --silent --show-error --max-time 10 \
  -o /dev/null -w 'HTTP %{http_code}\n' http://172.104.229.93/
```

On Linode:

```bash
docker inspect twn-recovery-website \
  --format 'State={{.State.Status}} Started={{.State.StartedAt}}'
```

Capture a redacted terminal log and both Telegram messages as badge
evidence; do not commit bot tokens, full environment dumps or SSH keys.

## Important limitations

- Public HTTP on a temporary learning server is not production TLS.
- The action is a **container restart**, not a Linode/server reboot.
- Restart action success does not prove functional recovery; only a fresh HTTP 200 does.
- The initial server script can be manually executed only by the already-authorized SSH user; it does not enforce a privilege boundary against that user.
- Before deleting the Linode, collect evidence; then review API tokens and billing.
