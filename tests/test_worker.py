import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class WorkerTests(unittest.TestCase):
    def test_preflight_and_persistent_simulator_cycle(self):
        with tempfile.TemporaryDirectory() as temp:
            env = dict(os.environ, AUTOMATION_DATA_DIR=temp)
            def run(*args):
                return subprocess.run([sys.executable, "-m", "mobile_automation.worker", *args],
                                      env=env, text=True, capture_output=True, timeout=10)
            self.assertEqual(run("--preflight").returncode, 0)
            self.assertFalse((Path(temp) / "workflow_state.json").exists())
            result = run("--once")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "completed")
            self.assertEqual(json.loads((Path(temp) / "workflow_state.json").read_text())["synthetic_claim"]["status"], "completed")

    def test_invalid_interval_fails(self):
        result = subprocess.run([sys.executable, "-m", "mobile_automation.worker", "--interval", "0"],
                                capture_output=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
