# macOS automation deployment

Reusable deployment infrastructure for a private Python automation service.
This repository contains deployment code only: no bot, simulator, game assets,
production inventory, or credentials.

The application stays in a separate private repository. This public project
documents and tests the infrastructure used to install and manage it on macOS.

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

## Repository layout

- [deployment/ansible](deployment/ansible): reusable role, playbook, and example configuration.
- [deployment/workflows](deployment/workflows): inactive CI/CD example for a trusted private repository.
- [tests](tests): deployment template and safety checks, not bot tests.
- [.github/workflows](.github/workflows): hosted validation only; no production deployment.

There is no application source or demo to run from this repository.

## Using the deployment role

1. Pin this repository to a reviewed commit in your private deployment project.
2. Supply your application repository, revision, Python entry point, and private settings.
3. Run Ansible against the Mac as its logged-in GUI user.

The LaunchAgent starts at user login and restarts after a non-zero exit. It runs
the revision installed by Ansible; it does not pull new code at every startup.
Updates happen through another deployment. Runtime state and configuration stay
outside the application checkout.

Keep real inventory and secrets private. The workflow example must be adapted
before use and should never expose a production runner to public pull requests.

## Test locally

```bash
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests
```

Tests check plist rendering and restart settings, shell syntax, and the presence
of preflight and deployment-lock cleanup. They do not verify a live application,
connected phone, or production Mac.

Ansible syntax and lint checks require a Linux/macOS controller (or WSL).
The managed service target is macOS; template tests also run on Linux and Windows.
