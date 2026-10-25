#!/usr/bin/env bash
# Fixed, narrowly scoped recovery command for the disposable CAP06 website.
# Installed manually to /root/cap06-recover-website.sh on the dedicated Linode.
set -Eeuo pipefail

readonly NAME=twn-recovery-website
readonly PROJECT=twn-capstone06

(( EUID == 0 )) || { echo "Run as the root lab user" >&2; exit 1; }
command -v docker >/dev/null || { echo "Docker is unavailable" >&2; exit 1; }

# Refuse to affect a missing or unrelated container.
docker container inspect "$NAME" >/dev/null 2>&1 || {
  echo "Lab website container not found" >&2; exit 1;
}
actual_name="$(docker inspect "$NAME" --format '{{.Name}}')"
label="$(docker inspect "$NAME" --format '{{index .Config.Labels "dev.twn.capstone"}}')"
project="$(docker inspect "$NAME" --format '{{index .Config.Labels "com.docker.compose.project"}}')"
[[ "$actual_name" == "/$NAME" && "$label" == "06" && "$project" == "$PROJECT" ]] || {
  echo "Container authorization check failed" >&2; exit 1;
}

docker container restart --timeout 5 "$NAME" >/dev/null
echo "CAP06 Docker restart command accepted; monitor must verify HTTP 200 separately"
