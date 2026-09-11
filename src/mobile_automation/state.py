import json
from pathlib import Path
from typing import Any


class JsonStateStore:
    """Atomic-enough small state file kept outside the deployed source tree."""

    def __init__(self, data_dir: Path) -> None:
        self.path = data_dir / "workflow_state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def write(self, state: dict[str, Any]) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.path)
