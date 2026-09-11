import tempfile
import unittest
from pathlib import Path

from mobile_automation.models import ActionStatus
from mobile_automation.simulator import SimulatedDevice
from mobile_automation.state import JsonStateStore
from mobile_automation.workflow import ConfirmedWorkflow


class ConfirmedWorkflowTests(unittest.TestCase):
    def workflow(self, device):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        return ConfirmedWorkflow(device, JsonStateStore(Path(directory.name)))

    def test_records_completed_action_only_after_postcondition(self):
        device = SimulatedDevice(
            ["base", "reward_panel"],
            {("reward_panel", "claim"): "reward_confirmed"},
        )
        workflow = self.workflow(device)
        result = workflow.perform(
            name="claim", expected_screen="reward_panel", target="claim",
            postcondition=lambda screen: screen == "reward_confirmed",
        )
        self.assertEqual(result.status, ActionStatus.COMPLETED)
        self.assertEqual(device.taps, [("reward_panel", "claim")])
        self.assertEqual(workflow.state.read()["claim"]["status"], "completed")

    def test_never_taps_when_expected_screen_is_not_observed(self):
        device = SimulatedDevice(["base", "world", "base"], {})
        result = self.workflow(device).perform(
            name="claim", expected_screen="reward_panel", target="claim",
            postcondition=lambda screen: screen == "reward_confirmed",
        )
        self.assertEqual(result.status, ActionStatus.UNAVAILABLE)
        self.assertEqual(device.taps, [])

    def test_postcondition_failure_is_not_reported_as_success(self):
        device = SimulatedDevice(["reward_panel"], {})
        result = self.workflow(device).perform(
            name="claim", expected_screen="reward_panel", target="claim",
            postcondition=lambda screen: screen == "reward_confirmed",
        )
        self.assertEqual(result.status, ActionStatus.FAILED)
        self.assertEqual(len(device.taps), 1)
