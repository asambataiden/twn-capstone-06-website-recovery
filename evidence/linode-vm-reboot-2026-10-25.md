# Linode VM reboot and website restoration — 2026-10-25

## Tested target

- Dedicated TWN Capstone 06 Linode: `twn-capstone06-webserver`, instance `109140229`, region `eu-central`.
- Docker Compose lab website: `twn-recovery-website`, restart policy `unless-stopped`.
- Reboot requested using the repository's `LinodeServerRebooter`, after an authenticated API read of the exact instance, IP check and operator confirmation `REBOOT LINODE 109140229`.

## Verified evidence (operator-supplied terminal output)

**API reboot response:**

```text
Verified server:
Label: twn-capstone06-webserver
Instance ID: 109140229
Region: eu-central
WARNING: This will reboot the entire Linode VM.
Type REBOOT LINODE 109140229: [confirmation entered]
SUCCESS: Linode API accepted reboot request.
```

**Boot time changed:** earlier `2026-10-25 04:06:31`, afterward `2026-10-25 05:42:59` (as reported by `uptime -s`).

**Post-reboot host/application validation:**

```text
systemctl is-active docker -> active
docker inspect twn-recovery-website -> State=running Policy=unless-stopped
curl http://127.0.0.1/ -> HTTP 200
```

An external Mac `curl` returned HTTP 200 in the submitted outputs. Its position relative to the reboot is not conclusively established by the pasted terminal excerpts, so do **not** cite it as a separately timestamped post-reboot external probe.

## Scope and limitations

**Proven:** a deliberate, authorized Linode API VM reboot request was accepted; the host's boot timestamp subsequently changed; Docker started, the previously running Nginx container was running with `unless-stopped`, and loopback HTTP returned 200.

**Not proven in this VM-reboot test:** the monitor captured a failure/healthy transition or sent Telegram `ALERT` and `RECOVERED` during this reboot. The monitor's only visible messages were `Monitoring Linode reboot...` and `Monitoring completed.`. A temporary outage shorter than the detection threshold, or timing outside the monitor's execution window, could explain the missing alert; the supplied logs do not distinguish these cases.

**Not proven:** automatic fallback from a failed remote Docker/SSH attempt to an unattended Linode VM reboot. The reboot here was **manually authorized via the API**, not triggered by the monitor.

The separate [verified live Docker recovery evidence](linode-live-recovery-2026-10-25.md) does document real HTTP incident detection, mobile Telegram messages, remote SSH Docker restart, and recovery confirmation. Do not conflate that experiment with this VM reboot.

## Badge-validation wording

I deployed an Nginx website in Docker on Linode and implemented Python HTTP health checks, Telegram notifications, and SSH-based Docker recovery. During a controlled live container outage, the monitor detected repeated failures, delivered an alert, restarted the Docker website on the remote Linode host, verified successful HTTP recovery, and sent a recovery notification. I also used a separately authorized Linode API call to reboot the VM and verified that Ubuntu, Docker, and the website returned with HTTP 200. I learned Docker restart policies, cloud API authentication, safe SSH automation, outage detection, alerting, recovery verification and evidence-based troubleshooting. The VM-reboot test was supervised; unattended VM reboot escalation was not demonstrated.
