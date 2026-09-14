# macOS automation deployment

Reusable deployment infrastructure for a private Python automation service.
This repository contains deployment code only: no bot, simulator, game assets,
production inventory, or credentials.

## Included

- Ansible role for Python dependencies and reviewed Git revisions.
- LaunchAgent startup at login and restart after failure.
- External configuration/state, optional Vault secrets, and state migration.
- Advisory preflight checks and log rotation.
- Hosted CI for Ansible validation and cross-platform template tests.
- Inactive private deployment workflow example.

See [deployment instructions](deployment/README.md) for configuration and use.
Consumers supply their own application repository and Python entry point.
Public CI has no production access.

## Test locally

```bash
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests
```

Ansible syntax and lint checks require a Linux/macOS controller (or WSL).
The managed service target is macOS; template tests also run on Linux and Windows.
