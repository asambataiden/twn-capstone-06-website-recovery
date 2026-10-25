# Capstone 06 — Verified Linode website-recovery evidence

**Exercise date:** 2026-10-25 (operator-provided terminal logs and Telegram screenshot)  
**GitHub implementation:** `feat/cap06-ssh-remote-docker-recovery` (merged in PR #5)  
**Scope:** disposable Linode Ubuntu 24.04 AMD64 VM, Docker Engine, Nginx Compose project `twn-capstone06`, Python health monitor on macOS, SSH recovery, Telegram mobile notifications.

## Evidence received

1. Docker Compose deployed the labelled container `twn-recovery-website`; the server and Mac independently reported HTTP 200 before fault injection.
2. Python tests on the feature branch: **35 passed in 0.06s**.
3. Linode recovery script passed `bash -n`. Docker metadata was confirmed:
   `Name=/twn-recovery-website Project=twn-capstone06 Capstone=06`.
4. SSH connectivity verified with strict host-key checking: `SSH recovery connection OK`.
5. During the controlled outage, the macOS Python monitor generated this sequence (timestamps from provided terminal output):

   ```text
   2026-10-25 06:05:10,564 WARNING UNHEALTHY: status_code=None error=URLError consecutive_failures=1
   2026-10-25 06:05:12,664 WARNING UNHEALTHY: status_code=None error=URLError consecutive_failures=2
   2026-10-25 06:05:14,805 WARNING UNHEALTHY: status_code=None error=URLError consecutive_failures=3
   2026-10-25 06:05:14,805 ERROR ALERT: failure threshold reached (3)
   2026-10-25 06:05:15,032 WARNING RECOVERY: attempting Docker container restart
   2026-10-25 06:05:16,322 INFO RECOVERY ACTION COMPLETED: waiting for health verification
   2026-10-25 06:05:18,437 INFO RECOVERED: website is healthy again
   Monitoring session completed.
   ```

6. Operator-supplied phone screenshot displayed **ALERT** and **RECOVERED** Telegram messages for the public Linode website. The screenshot remains in the conversation; it has **not** been uploaded to this repository.
7. Operator independently demonstrated HTTP 200 on the public website and on Linode loopback; the successful external probe in the supplied output was not simultaneous with the recovered-event log. The monitoring loop itself confirmed a successful post-restart HTTP check.
8. **Important later action:** after the successful demonstration, the user ran `docker stop twn-recovery-website` again. Current live availability is therefore **not established** by this evidence; restore and retest before further work.

## What this proves

- A real Linode-hosted Docker/Nginx application was deployed and reached from macOS.
- The existing Python monitor detected three consecutive failed HTTP checks.
- Telegram mobile alert and recovery notifications appeared on the operator's phone.
- The SSH remote recovery action completed successfully.
- The Python monitor subsequently observed the website healthy again.

## Not yet proven

- **Linode VM reboot recovery:** the optional Linode API reboot adapter has offline unit tests, but no authorized live VM reboot / full end-to-end recovery evidence.
- Production hardening, persistent incident state, or production availability guarantees.
- A screenshot or independently archived artifact uploaded into GitHub from the phone (operator retains screenshot).
- Review acceptance by TWN badge assessors.

## Suggested truthful validation-form answer

I built and tested a Python website-monitoring and recovery workflow for an Nginx application hosted on a Linode cloud server in Docker. The monitor runs on my Mac, checks HTTP availability, detects three consecutive failures, and sends a Telegram alert to my phone. In a live controlled outage, the monitor used authenticated SSH to run a guarded Docker restart on the Linode server. A subsequent HTTP check confirmed that the website recovered, and a Telegram recovery notification arrived on my phone. The project includes version-controlled Docker setup and deployment scripts, unit tests, and recovery runbooks. I learned how to connect HTTP monitoring, mobile notifications, Linux server management, Docker, SSH, and automated incident recovery. The separate cloud-server reboot path is implemented as an opt-in adapter but has not yet been live-validated.

## Evidence handling

Do not commit SSH keys, bot tokens, private chats or full environment dumps. Before including phone screenshots, review whether chat names, times, unrelated messages or identifiable information must be cropped or redacted.
