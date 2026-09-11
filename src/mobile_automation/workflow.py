from collections.abc import Callable

from .device import DeviceClient
from .models import ActionResult, ActionStatus
from .state import JsonStateStore


class ConfirmedWorkflow:
    """Runs one action only when pre- and postconditions can be observed."""

    def __init__(self, device: DeviceClient, state: JsonStateStore, max_observations: int = 3) -> None:
        self.device = device
        self.state = state
        self.max_observations = max_observations

    def perform(
        self,
        *,
        name: str,
        expected_screen: str,
        target: str,
        postcondition: Callable[[str], bool],
    ) -> ActionResult:
        for attempt in range(1, self.max_observations + 1):
            screen = self.device.observe()
            if screen != expected_screen:
                continue

            self.device.tap(target)
            after = self.device.observe()
            if postcondition(after):
                result = ActionResult(
                    ActionStatus.COMPLETED,
                    f"{name} confirmed by postcondition",
                    attempt,
                    {"before": screen, "after": after},
                )
                self._record(name, result)
                return result

            result = ActionResult(
                ActionStatus.FAILED,
                f"{name} tap did not produce its expected state",
                attempt,
                {"before": screen, "after": after},
            )
            self._record(name, result)
            return result

        result = ActionResult(
            ActionStatus.UNAVAILABLE,
            f"{name} did not observe {expected_screen!r}",
            self.max_observations,
        )
        self._record(name, result)
        return result

    def _record(self, name: str, result: ActionResult) -> None:
        state = self.state.read()
        state[name] = {
            "status": result.status,
            "detail": result.detail,
            "attempts": result.attempts,
            "evidence": result.evidence,
        }
        self.state.write(state)
