# Security and Production-Readiness Assessment

## 1. Security scope

This is an educational, locally operated monitoring/recovery controller. It is **not** a hardened, autonomous production remediation system. Applying its Docker recovery adapter to non-lab workloads is outside the demonstrated scope.

## 2. Implemented safeguards

| Control | Current behavior | Residual risk |
| --- | --- | --- |
| HTTP scheme validation | Probe allows HTTP(S) | No destination-IP, redirect or hostname allowlist protection |
| Bounded HTTP operation | Timeout passed to urllib | Timeout is not a guaranteed full end-to-end deadline |
| Alert deduplication | One alert per in-memory incident | Restarting monitor resets state |
| Recovery attempt bound | One Docker restart attempt per in-memory incident | No durable rate limit across monitor restarts |
| Docker command construction | `subprocess.run` argument list, no shell | Docker daemon API remains high privilege |
| Docker target format | Names must begin `twn-recovery-` | Name pattern is not container ownership proof |
| Disposable lab authorization | Name, label, policy and state checked in lab caller | Time-of-check/time-of-use window; not rechecked inside adapter |
| Notification credentials | Read from environment variables | Environment may be exposed to same-user processes, debugging or operational tooling |
| Error isolation | Notification/recovery exceptions do not stop monitoring | Downstream delivery or remediation can still fail |
| Error sanitization | Telegram/Docker adapter error messages avoid raw HTTP/CLI error text | Proxy logs and third-party traces may still contain sensitive URLs |
| Loopback publishing | Demo binds `127.0.0.1:18080` | Host-level Docker/network configuration still matters |

## 3. Threat model

### Untrusted monitoring destinations / SSRF

Do not expose the monitored URL as a publicly writable parameter. A user-controlled URL could cause requests to localhost, internal services, cloud metadata endpoints or redirected destinations. For a service deployment, enforce an explicit host allowlist and carefully validate resolved IPs and redirects.

### Docker daemon authority

Access to Docker generally permits extensive control over host workloads and data. Avoid mounting a Docker socket into public-facing containers. A production alternative is a narrowly scoped recovery controller or agent with audited authorization and specific allowed operations. Container **names** alone are not a sufficient authorization boundary.

### Telegram bot secret handling

Do not commit credentials, print complete Bot API URLs, share tokens in screenshots or put them in tracked `.env` files. Use a trusted secret-management system in deployed environments. Rotate compromised tokens via BotFather. Consider HTTPS proxy logging and process environment visibility.

### Recovery loops and service stability

The monitor allows one recovery attempt per incident while running. Process restart resets incident state and could trigger another attempt for the same ongoing outage. Production deployment needs persistent incident state, retry budgets, cooldowns, maintenance windows and operator override controls.

## 4. Operational limitations

- Synchronous monitoring: notification send and Docker restart can delay checks.
- No persistent audit/event store.
- No concurrency control or leader election across multiple monitor instances.
- No notification delivery queue, exponential backoff, or guaranteed delivery.
- No production-grade readiness check, metrics, tracing or service-level objective policy.
- `HTTP 200` is a simplistic availability signal, not complete functional health.
- The local lab uses `nginx:alpine` as a floating tag; pin and review an immutable digest for controlled environments.
- A successful Docker restart command does not prove successful service recovery.

## 5. Production-hardening backlog (not yet implemented)

1. Bind an exact approved service/resource identity to an immutable configuration and enforce authorization inside the recovery adapter.
2. Limit Docker authority through a narrowly scoped service account or dedicated recovery agent.
3. Persist incident state, recovery attempts, cooldowns and audit history.
4. Pin image digests, scan the runtime image and document patch ownership.
5. Introduce structured logs, metrics, alerts and a runbook-driven escalation path.
6. Restrict target URLs with allowlists, redirect policy and network controls.
7. Separate credentials from application configuration and implement rotation.
8. Add deployment supervision, termination handling and automated integration testing in an isolated environment.

## 6. Evidence handling

Before committing evidence, redact tokens, private identifiers, personal chat details, workstation-specific sensitive paths and any non-lab container metadata. Check staged content with `git diff --cached` and inspect file changes before publishing.
