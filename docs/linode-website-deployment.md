# Linode Website Deployment — Capstone 06

## Prerequisites

- Dedicated Ubuntu 24.04 AMD64 Linode, Docker Engine and Compose already installed.
- Linode Cloud Firewall reviewed **before exposing port 80**: allow SSH only from an authorized management IP, TCP 80 as required for demonstration, deny other unsolicited inbound traffic.
- Do not use this on shared, production, or existing customer infrastructure.
- Web service publicly publishes HTTP on port 80. This is an **educational temporary endpoint**, not a secure production service.

## Deploy from macOS

On Mac, on branch `feat/cap06-linode-nginx-compose`:

```bash
scp -o IdentitiesOnly=yes -i ~/.ssh/id_ed25519_github_asambataiden \
  deploy/linode/compose.yaml deploy/linode/deploy-website.sh \
  root@172.104.229.93:/root/
ssh -o IdentitiesOnly=yes -i ~/.ssh/id_ed25519_github_asambataiden \
  root@172.104.229.93
```

On Linode:

```bash
cd /root
bash -n deploy-website.sh
docker compose -p twn-capstone06 -f compose.yaml config --quiet
bash deploy-website.sh --deploy
docker inspect twn-recovery-website --format 'Name={{.Name}} State={{.State.Status}} Policy={{.HostConfig.RestartPolicy.Name}} Label={{index .Config.Labels "dev.twn.capstone"}}'
curl --noproxy '*' --fail --silent --show-error --max-time 5 http://127.0.0.1/ -o /dev/null -w 'HTTP %{http_code}\n'
```

From Mac (external path):

```bash
curl --fail --silent --show-error --max-time 10 \
  -o /dev/null -w 'HTTP %{http_code}\n' http://172.104.229.93/
```

Only treat deployment as verified after the actual server and external HTTP probes succeed. Do not commit runtime credentials, raw IP-based evidence that the user prefers to keep private, or personal Telegram IDs.

## Recovery implications

This Compose service uses `restart: unless-stopped` so it can return after a host reboot, but it remains stopped after an explicit operator `docker stop` until restarted manually or through the Python recovery controller. The existing Python `DockerRestarter` runs locally; **it does not remotely control this Linode**. Remote recovery must be added and tested before calling the website-monitoring flow complete. The optional Linode reboot adapter also requires explicit authorization and will **never** run as part of this deployment.

The local-only recovery runbook in `docs/deployment-runbook.md` is intentionally preserved and unchanged.

## Cleanup (only for the dedicated lab)

Confirm the Compose project and `dev.twn.capstone=06` label before deleting any resource. From `/root`:

```bash
docker compose -p twn-capstone06 -f compose.yaml ps
docker inspect twn-recovery-website --format '{{index .Config.Labels "dev.twn.capstone"}}'
docker compose -p twn-capstone06 -f compose.yaml down
```

Removing the Docker container does not stop Linode billing. Delete the separate disposable Linode after collecting evidence, if it is no longer needed.
