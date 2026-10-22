# Architecture — Website Monitoring and Recovery

## 1. Purpose and scope

A small synchronous Python controller periodically checks one trusted HTTP(S) endpoint. It detects sustained failure, sends one alert per incident, optionally attempts one Docker restart, and reports recovery only after a later successful HTTP check.

## 2. Components

| Component | File | Responsibility |
| --- | --- | --- |
| HTTP probe | `src/website_recovery/health.py` | GET a URL and return `HealthCheckResult(healthy, status_code, error)` |
| Incident loop | `src/website_recovery/monitor.py` | Consecutive failure counter, active-incident state, timing and integration hooks |
| Notification contract | `src/website_recovery/notifications.py` | `Notifier` protocol, `Notification`, `EventType`, `LoggingNotifier` |
| Telegram adapter | `src/website_recovery/telegram.py` | Send a JSON `sendMessage` HTTPS POST with credentials from environment |
| Docker adapter | `src/website_recovery/recovery.py` | Run an explicitly named `docker container restart` using `subprocess.run` |
| Tests | `tests/` | Mocked network/CLI behavior and incident transitions |

## 3. Incident lifecycle

```text
INITIAL / HEALTHY
    | unhealthy result
    v
DEGRADED (consecutive_failures += 1)
    | healthy -> reset count; no incident
    | threshold met, incident_active == false
    v
INCIDENT ACTIVE
    | emit ALERT (one per incident)
    | optionally attempt Docker restart (one attempt)
    | further unhealthy results -> no duplicate alert/restart
    | first later healthy result
    v
RECOVERED
    | reset consecutive_failures and incident_active
    | emit RECOVERED
    v
READY FOR FUTURE INCIDENT
```

Incident state currently exists only in memory. If the process restarts during an outage, its counters and `incident_active` state reset. This can lead to repeat alerts/restarts across process restarts.

## 4. State and failure behavior

- The current probe treats HTTP **200** as healthy. Other statuses and transport errors are unhealthy.
- A failure threshold is based on **consecutive completed checks**, not elapsed outage duration.
- `max_checks` is available for finite demonstrations and testing; the default monitor runs until interrupted.
- Notification adapter exceptions are logged, and checking continues; successful notification delivery is not guaranteed.
- Docker recovery adapter exceptions are logged, and checking continues.
- An executed Docker restart is **a remediation attempt**, not an application recovery event.
- The HTTP probe determines recovery independently of Docker command output.
- The monitor is single-threaded and synchronous; notification and restart operations delay subsequent checks.

## 5. Dependency boundaries

The monitor accepts a checker callback, sleeper callback, optional notifier, and optional restarter. This allows deterministic incident tests without network access, delays or Docker execution. The notification contract is provider-neutral; Telegram is one concrete adapter.

## 6. Trust boundaries

1. **Untrusted HTTP target:** The process performs outgoing HTTP(S) requests. The implementation validates the scheme but not destination IPs, redirects or private network access. Use a trusted configuration source; do not expose arbitrary URL control through an unauthenticated interface.
2. **Telegram provider:** The bot token is a secret. HTTPS transport, request timeouts and sanitized adapter errors reduce—but do not eliminate—risk. Token-bearing URLs can still surface in infrastructure/proxy tracing.
3. **Docker daemon:** The Docker CLI invokes a highly privileged API. The current adapter checks container name format, not resource ownership. An external one-time lab check validates label, state and policy; a production boundary would need to verify container identity/ownership at invocation and constrain daemon permissions.
4. **Process logs:** Error traces and application URLs can contain confidential details. Use appropriate log access controls and redaction.

## 7. Non-goals and next improvements

This is not a Kubernetes operator, high-availability controller, or orchestrated remediation platform. Potential future improvements include persistent incident state, explicit recovery rate limits across restarts, Docker SDK resource identity validation, least-privilege recovery agent, bounded queuing and delivery retries, active health/readiness endpoints, metrics, structured audit events and declarative deployment.
