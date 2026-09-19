import os
import plistlib
import shlex
import shutil
import subprocess
import unittest
from pathlib import Path

try:
    import jinja2
    import yaml
except ImportError:
    jinja2 = None

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(jinja2 is None, "Jinja2 and PyYAML required")
class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(ROOT / "deployment/ansible/roles/automation/templates"),
            undefined=jinja2.StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.filters["quote"] = shlex.quote
        self.values = {
            "automation_data_dir": "/Users/Demo & Test/Library/Application Support/Worker",
            "automation_repo_dir": "/Users/Demo & Test/Applications/Worker",
            "automation_home": "/Users/Demo & Test", "automation_label": "org.example.worker",
            "automation_brew_prefix": "/opt/homebrew", "automation_retry_seconds": 60,
            "automation_path": "/usr/bin:/bin", "automation_arguments": ["/Applications/Example App/main.py"],
            "automation_launcher": "",
            "automation_preflight_arguments": ["--preflight"], "automation_environment": {},
            "automation_secrets": {"EXAMPLE": "spaces ' quotes & symbols"},
        }

    def test_plists_escape_paths_and_restart_on_failure(self):
        agent = plistlib.loads(self.env.get_template("worker.plist.j2").render(**self.values).encode())
        self.assertEqual(agent["ProgramArguments"][1], self.values["automation_data_dir"] + "/run_worker.sh")
        self.assertTrue(agent["RunAtLoad"])
        self.assertFalse(agent["KeepAlive"]["SuccessfulExit"])
        rotation = plistlib.loads(self.env.get_template("logrotate.plist.j2").render(**self.values).encode())
        self.assertEqual(rotation["StartInterval"], 3600)

    def test_shell_templates_parse(self):
        bash = r"C:\Program Files\Git\bin\bash.exe" if os.name == "nt" else shutil.which("bash")
        if not bash or not Path(bash).exists():
            self.skipTest("Bash required")
        for template in ("run_worker.sh.j2", "worker.env.j2"):
            source = self.env.get_template(template).render(**self.values)
            result = subprocess.run([bash, "-n"], input=source, text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_preflight_arguments_remain_separate_from_fi(self):
        source = self.env.get_template("run_worker.sh.j2").render(**self.values)
        self.assertIn('--preflight\nfi', source)

    def test_worker_delegates_to_an_optional_application_launcher(self):
        source = self.env.get_template("run_worker.sh.j2").render(
            **(self.values | {"automation_launcher": "/Applications/Example App/run.sh"})
        )
        self.assertIn("launcher='/Applications/Example App/run.sh'", source)
        self.assertIn('exec "$launcher" "$@"', source)

    def test_preflight_is_in_tasks_and_lock_has_cleanup(self):
        tasks = yaml.safe_load((ROOT / "deployment/ansible/roles/automation/tasks/main.yaml").read_text())
        block = next(t for t in tasks if "block" in t)
        self.assertTrue(any("preflight" in t["name"].lower() for t in block["block"]))
        self.assertIn("always", block)

    def test_migration_check_is_a_minimal_existence_probe(self):
        tasks = yaml.safe_load((ROOT / "deployment/ansible/roles/automation/tasks/migrate.yaml").read_text())
        check = tasks[0]
        self.assertEqual(check["ansible.builtin.command"]["argv"][:2], ["/bin/test", "-e"])
        self.assertFalse(check["changed_when"])
        self.assertFalse(check["failed_when"])
