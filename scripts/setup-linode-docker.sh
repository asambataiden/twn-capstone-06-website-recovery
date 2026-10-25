#!/usr/bin/env bash
# TWN Capstone 06: reproducible Docker setup for a fresh Linode Ubuntu 24.04 host.
# Usage: sudo bash scripts/setup-linode-docker.sh --check | --install
# Scope: Docker Engine/Compose only. No firewall, SSH, nginx, or cloud actions.
set -Eeuo pipefail

readonly REPO_FILE="/etc/apt/sources.list.d/docker.sources"
readonly KEY_FILE="/etc/apt/keyrings/docker.asc"

log() { printf '[cap06-docker] %s\n' "$*"; }
die() { printf '[cap06-docker] ERROR: %s\n' "$*" >&2; exit 1; }

usage() {
  printf 'Usage: %s --check|--install\n' "$0" >&2
  exit 2
}

check_host() {
  [[ -r /etc/os-release ]] || die "Cannot read /etc/os-release"
  # shellcheck disable=SC1091
  source /etc/os-release
  [[ "${ID:-}" == "ubuntu" && "${VERSION_ID:-}" == "24.04" ]] ||
    die "This script supports Ubuntu 24.04 only"
  [[ "$(dpkg --print-architecture)" == "amd64" ]] ||
    die "This lab script supports amd64 only"
  command -v apt-get >/dev/null || die "apt-get unavailable"
}

report() {
  log "OS: $(. /etc/os-release; printf '%s' "$PRETTY_NAME")"
  log "Architecture: $(dpkg --print-architecture)"
  if command -v docker >/dev/null 2>&1; then
    docker --version
    docker compose version || true
    systemctl is-active docker || true
    systemctl is-enabled docker || true
  else
    log "Docker not installed"
  fi
  if [[ -e "$REPO_FILE" ]]; then
    log "Docker APT source file exists"
  else
    log "Docker APT source file is absent"
  fi
  log "Firewall state was not changed; check Linode Cloud Firewall separately"
}

install_docker() {
  (( EUID == 0 )) || die "Run with sudo/root"
  # Do not silently remove or replace existing Docker installations.
  for pkg in docker.io docker-compose docker-compose-v2 podman-docker containerd runc; do
    if dpkg-query -W -f='${db:Status-Status}' "$pkg" 2>/dev/null |
        grep -qx installed; then
      die "Conflicting installed package: $pkg. Review existing installation first."
    fi
  done
  if [[ -e "$REPO_FILE" ]] &&
      ! grep -Fq 'URIs: https://download.docker.com/linux/ubuntu' "$REPO_FILE"; then
    die "Docker repository file exists with unexpected content. Review manually."
  fi

  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y --no-install-recommends ca-certificates curl

  install -m 0755 -d /etc/apt/keyrings
  if [[ ! -s "$KEY_FILE" ]]; then
    local tmp
    tmp="$(mktemp /etc/apt/keyrings/docker.asc.XXXXXX)"
    if ! curl --fail --show-error --silent --location \
      https://download.docker.com/linux/ubuntu/gpg -o "$tmp"; then
      rm -f "$tmp"
      die "Could not download Docker repository signing key"
    fi
    chmod 0644 "$tmp"
    mv "$tmp" "$KEY_FILE"
  fi

  if [[ ! -e "$REPO_FILE" ]]; then
    cat > "$REPO_FILE" <<'EOF'
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: noble
Components: stable
Architectures: amd64
Signed-By: /etc/apt/keyrings/docker.asc
EOF
    chmod 0644 "$REPO_FILE"
  fi

  apt-get update
  apt-get install -y --no-install-recommends \
    docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  systemctl enable --now docker

  systemctl is-active --quiet docker || die "Docker service is not active"
  docker version >/dev/null || die "Docker CLI cannot contact daemon"
  docker compose version || die "Docker Compose plugin is missing"

  log "Installed package versions:"
  dpkg-query -W -f='${binary:Package} ${Version}\n' \
    docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  log "Running isolated official hello-world test"
  docker run --rm hello-world
  log "Docker setup successful. No website or cloud firewall resources were changed."
}

[[ $# == 1 ]] || usage
check_host
case "$1" in
  --check) report ;;
  --install) install_docker ;;
  *) usage ;;
esac
