# Verified Live Linode Fallback — 2026-10-25

**Exercise:** TWN Capstone 06, automatic **code-path escalation** from simulated primary Docker recovery failure to a real Linode VM reboot.  
**Implementation:** `scripts/verify-linode-fallback.py`, `DockerThenLinodeRecovery`, `LinodeServerRebooter`.  
**Environment:** Dedicated Linode `twn-capstone06-webserver`, ID `109140229`, Frankfurt (`eu-central`); Docker/Nginx website `twn-recovery-website`; macOS Python monitor; Telegram mobile notifications.

## Verified operator-provided results

- Feature branch checkout and dependency sync succeeded.
- **35 tests passed in 0.05s.**
- Safe preview output confirmed target and marked the primary Docker failure as simulated; no live action during preview.
- Live test (`--execute`) verified Linode ID, IP, label, region and running status, required the exact typed `REBOOT LINODE 109140229` confirmation, then reported:

```text
Executing controlled fallback...
[LAB] Injected Docker RecoveryError (simulation).
SUCCESS: fallback issued Linode API reboot request.
API acceptance is not proof of successful VM/website recovery.
```

- Independent macOS monitor recorded a real HTTP outage and recovery:

```text
2026-10-25 06:57:34,464 WARNING UNHEALTHY: status_code=None error=URLError consecutive_failures=1
2026-10-25 06:57:36,512 WARNING UNHEALTHY: status_code=None error=URLError consecutive_failures=2
2026-10-25 06:57:36,512 ERROR ALERT: failure threshold reached (2)
2026-10-25 06:58:25,915 WARNING UNHEALTHY: status_code=None error=URLError consecutive_failures=12
2026-10-25 06:58:27,986 INFO RECOVERED: website is healthy again
```

- Phone screenshot supplied during the conversation showed Telegram **ALERT at 06:57** and **RECOVERED at 06:58** for the Linode website; screenshot intentionally not committed because unrelated personal chat material is visible.
- Previous VM boot timestamp (from operator output): `2026-10-25 05:42:59` UTC. New boot timestamp after this test: **`2026-10-25 05:58:18` UTC**. SSH disconnected during the reboot and the operator reconnected.
- After reboot, on Linode: `systemctl is-active docker` → **active**; website `State=running Policy=unless-stopped`; local `curl` → **HTTP 200**.
- On Mac, external `curl` after the test → **HTTP 200**.

## Conclusions and evidence boundary

**Verified:** Automated execution of the existing `DockerThenLinodeRecovery` fallback when its primary adapter raises `RecoveryError`; the fallback issued a real Linode reboot request. The reboot occurred (changed host boot timestamp) and the Docker website recovered to HTTP 200; Telegram mobile alerts tracked the real outage and recovery.

**Simulated:** The primary Docker/SSH failure was deliberately **injected**, not a natural fault. This is **not** a demonstration of an independently observed real SSH outage, production-grade unattended diagnosis, or persistent recovery policy across controller restarts.

**Authorization:** The script was manually started with `--execute` and required typed approval before initiating a real VM reboot. Once authorized, the primary-failure-to-Linode API fallback action was automatic.

**Separate live evidence:** Earlier [real container-stop and automated SSH Docker recovery](linode-live-recovery-2026-10-25.md) and [supervised Linode reboot verification](linode-vm-reboot-2026-10-25.md). These tests together cover different recovery paths and must not be conflated.

## Suggested TWN form answer

I built a Python website monitoring and automated recovery system for a Docker-hosted Nginx website on a Linode cloud VM. It checks HTTP availability, notifies me on Telegram when repeated failures occur, restarts the remote Docker application over authenticated SSH, and sends a recovery notification after an HTTP health check succeeds. I verified this with a live container outage and subsequent automatic application restoration. I separately verified a supervised Linode VM reboot and tested my recovery fallback by injecting a simulated Docker recovery failure: the existing Python code automatically requested a real Linode reboot, the server restarted, Docker and Nginx recovered, and I received both outage and recovery Telegram notifications. I learned incident detection, Linux/Docker recovery, SSH authentication, cloud APIs, restart policies, automated testing, and safe infrastructure recovery. The fallback exercise used a simulated primary failure, not an uncontrolled real SSH failure.

## Follow-up and resource hygiene

Only publish redacted screenshots and evidence. Never commit API/bot tokens or SSH private keys. Once TWN evidence is accepted and no additional experiment is needed, delete the temporary Linode and review billing / residual API tokens.
