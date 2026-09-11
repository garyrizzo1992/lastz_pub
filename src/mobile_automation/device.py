from typing import Protocol


class DeviceClient(Protocol):
    """Minimal adapter boundary for an ADB, Appium, or simulated device."""

    def observe(self) -> str:
        """Return a stable, classified screen identifier."""

    def tap(self, target: str) -> None:
        """Request a semantic action; adapters map it to concrete input."""
