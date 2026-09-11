from collections import deque


class SimulatedDevice:
    """A deterministic device for testing workflows without real hardware."""

    def __init__(self, screens: list[str], transitions: dict[tuple[str, str], str]) -> None:
        self._screens = deque(screens)
        self._current = self._screens.popleft() if self._screens else "unknown"
        self._transitions = transitions
        self.taps: list[tuple[str, str]] = []

    def observe(self) -> str:
        if self._screens:
            self._current = self._screens.popleft()
        return self._current

    def tap(self, target: str) -> None:
        self.taps.append((self._current, target))
        self._current = self._transitions.get((self._current, target), self._current)
