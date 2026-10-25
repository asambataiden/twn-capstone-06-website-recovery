#!/usr/bin/env python3
"""Controlled live validation of automatic Docker-error -> Linode-reboot fallback.

SIMULATION: The Docker recovery adapter deliberately raises RecoveryError.
REAL ACTION: If separately authorized, the Linode API reboots the lab VM.
This is NOT proof of an authentic Docker or SSH outage.
"""
import argparse
import getpass
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from website_recovery.cloud_recovery import DockerThenLinodeRecovery, LinodeServerRebooter
from website_recovery.health import check_website
from website_recovery.recovery import RecoveryError

INSTANCE_ID = 109140229
EXPECTED_IP = "172.104.229.93"
EXPECTED_REGION = "eu-central"
EXPECTED_LABEL = "twn-capstone06-webserver"
CONFIRMATION = f"REBOOT LINODE {INSTANCE_ID}"


class SimulatedFailedDockerRestarter:
    """Exercise the real fallback branch without modifying Docker or SSH."""

    def restart(self) -> None:
        print("[LAB] Injected Docker RecoveryError (simulation).", flush=True)
        raise RecoveryError("SIMULATED Docker recovery failure")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Request ONE live VM reboot after explicit approval; default is safe preview",
    )
    args = parser.parse_args()

    print("TARGET:", EXPECTED_LABEL, EXPECTED_REGION, EXPECTED_IP, INSTANCE_ID)
    print("PRIMARY FAILURE: injected (simulated).")
    print("FALLBACK: real Linode reboot through existing Python adapter.")
    if not args.execute:
        print("PREVIEW ONLY. Run with --execute only for the dedicated disposable lab VM.")
        return 0

    baseline = check_website(f"http://{EXPECTED_IP}/", timeout=5.0)
    if not baseline.healthy:
        print("ABORT: baseline website is not HTTP 200.", file=sys.stderr)
        return 1

    token = getpass.getpass("Linode API token (not stored): ").strip()
    if not token:
        print("ABORT: no token supplied.", file=sys.stderr)
        return 1

    request = Request(
        f"https://api.linode.com/v4/linode/instances/{INSTANCE_ID}",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urlopen(request, timeout=10) as response:
            instance = json.load(response)
    except HTTPError as exc:
        print(f"ABORT: Linode read API returned HTTP {exc.code}.", file=sys.stderr)
        return 1
    except (URLError, TimeoutError, OSError, ValueError):
        print("ABORT: Linode API lookup or response validation failed.", file=sys.stderr)
        return 1

    if not isinstance(instance, dict) or any((
        instance.get("id") != INSTANCE_ID,
        instance.get("label") != EXPECTED_LABEL,
        instance.get("region") != EXPECTED_REGION,
        instance.get("status") != "running",
        EXPECTED_IP not in instance.get("ipv4", []),
    )):
        print("ABORT: Linode identity/status mismatch.", file=sys.stderr)
        return 1

    print("Verified ID, IP, label, region, status=running.")
    print("WARNING: the next action will reboot this entire VM.")
    try:
        with open("/dev/tty", "r", encoding="utf-8") as tty:
            print(f"Type {CONFIRMATION}: ", end="", flush=True)
            answer = tty.readline().strip()
    except OSError:
        print("ABORT: an interactive terminal is required.", file=sys.stderr)
        return 1

    if answer != CONFIRMATION:
        print("ABORT: confirmation did not match.")
        return 1

    plan = DockerThenLinodeRecovery(
        docker_restarter=SimulatedFailedDockerRestarter(),
        linode_rebooter=LinodeServerRebooter(
            instance_id=INSTANCE_ID,
            api_token=token,
            confirmation=answer,
        ),
    )
    print("Executing controlled fallback...", flush=True)
    plan.restart()
    print("SUCCESS: fallback issued Linode API reboot request.", flush=True)
    print("API acceptance is not proof of successful VM/website recovery.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
