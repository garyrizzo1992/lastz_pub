from pathlib import Path
from tempfile import TemporaryDirectory

from mobile_automation.simulator import SimulatedDevice
from mobile_automation.state import JsonStateStore
from mobile_automation.workflow import ConfirmedWorkflow


with TemporaryDirectory(prefix="mobile-automation-demo-") as directory:
    device = SimulatedDevice(
        screens=["base", "reward_panel"],
        transitions={("reward_panel", "claim"): "reward_confirmed"},
    )
    workflow = ConfirmedWorkflow(device, JsonStateStore(Path(directory)))
    result = workflow.perform(
        name="claim_reward",
        expected_screen="reward_panel",
        target="claim",
        postcondition=lambda screen: screen == "reward_confirmed",
    )
    print(f"{result.status}: {result.detail}")
