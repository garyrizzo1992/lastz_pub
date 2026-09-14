"""A synthetic long-running worker. No network or real device access."""
import argparse
import json
import os
import signal
import threading
from datetime import datetime, timezone
from pathlib import Path

from .simulator import SimulatedDevice
from .state import JsonStateStore
from .workflow import ConfirmedWorkflow


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=60)
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be positive")
    data_dir = Path(os.environ.get("AUTOMATION_DATA_DIR", str(Path.home() / ".local/share/mobile-automation"))).expanduser()
    store = JsonStateStore(data_dir)
    if args.preflight:
        store.read()  # Invalid persisted JSON is a configuration failure.
        print("Preflight passed: simulator available; external state readable", flush=True)
        return
    stop = threading.Event()
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, lambda *_: stop.set())
    while not stop.is_set():
        device = SimulatedDevice(["reward_panel"], {("reward_panel", "claim"): "reward_confirmed"})
        result = ConfirmedWorkflow(device, store).perform(
            name="synthetic_claim", expected_screen="reward_panel", target="claim",
            postcondition=lambda screen: screen == "reward_confirmed",
        )
        print(json.dumps({"time": datetime.now(timezone.utc).isoformat(), "status": result.status, "detail": result.detail}), flush=True)
        if args.once:
            break
        stop.wait(args.interval)


if __name__ == "__main__":
    main()
