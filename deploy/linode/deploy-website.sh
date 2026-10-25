#!/usr/bin/env bash
# Deploy only the dedicated TWN Capstone 06 Nginx website.
# Run on the isolated Linode host, from a directory containing compose.yaml.
set -Eeuo pipefail

[[ $# == 1 && "$1" == "--deploy" ]] || {
  echo "Usage: bash deploy-website.sh --deploy" >&2; exit 2;
}
(( EUID == 0 )) || { echo "Run as root on the dedicated lab server" >&2; exit 1; }
command -v docker >/dev/null || { echo "Docker is missing" >&2; exit 1; }
docker compose version >/dev/null
[[ -f compose.yaml ]] || { echo "compose.yaml missing in current directory" >&2; exit 1; }

# Refuse to take ownership of an unrelated or manually created container.
if docker container inspect twn-recovery-website >/dev/null 2>&1; then
  label="$(docker container inspect --format '{{index .Config.Labels "dev.twn.capstone"}}' twn-recovery-website)"
  project="$(docker container inspect --format '{{index .Config.Labels "com.docker.compose.project"}}' twn-recovery-website)"
  [[ "$label" == "06" && "$project" == "twn-capstone06" ]] || {
    echo "Container name already belongs to a different workload; refusing deployment" >&2
    exit 1
  }
fi

# Ensure compose syntax is sound before creating resources.
docker compose -p twn-capstone06 -f compose.yaml config --quiet
docker compose -p twn-capstone06 -f compose.yaml up -d --no-build

# Nginx may take a moment to become available; allow a bounded retry window.
for attempt in {1..15}; do
  status="$(curl --noproxy '*' -sS --max-time 3 -o /dev/null -w '%{http_code}' http://127.0.0.1/ 2>/dev/null || true)"
  if [[ "$status" == "200" ]]; then
    echo "[cap06] Nginx HTTP 200 on loopback"
    docker compose -p twn-capstone06 -f compose.yaml ps
    exit 0
  fi
  sleep 2
done
echo "[cap06] Website did not return HTTP 200 in the validation window" >&2
docker compose -p twn-capstone06 -f compose.yaml ps
exit 1
