# Deploying the portfolio worker

This deploys the synthetic simulator shipped in this repository. It does not
connect to a phone, expose a network service, or contain production access.
The same role can deploy a different Python entry point through variables.

## Try on a Mac

Prerequisites: macOS, Homebrew, Git command-line tools, Python available for
Ansible, and a logged-in non-root GUI user. Automatic login works without a
physical monitor. The service starts at login, not before FileVault unlock.
Run from macOS or a Linux/WSL controller; Ansible does not run natively on Windows.

```bash
python3 -m venv .ansible-venv
.ansible-venv/bin/pip install ansible-core==2.19.3
.ansible-venv/bin/ansible-galaxy collection install -r deployment/ansible/requirements.yaml
.ansible-venv/bin/ansible-playbook -i deployment/ansible/inventory.example.ini deployment/ansible/playbook.yaml --syntax-check
.ansible-venv/bin/ansible-playbook -i deployment/ansible/inventory.example.ini deployment/ansible/playbook.yaml -e "automation_revision=$(git rev-parse HEAD)"
```

Defaults are in roles/worker/defaults/main.yaml. Copy vars.example.yaml to a local
settings.yaml to override paths or the revision; add -e @settings.yaml to the
command. For a remote Mac replace the localhost inventory entry with its private
hostname and SSH user. Do not commit real inventory or credentials.

The worker logs a simulated confirmed action once per minute and writes
workflow_state.json under ~/Library/Application Support/MobileAutomation.
No template matching, OCR or real-device adapter is implemented by this demo.
A semantic screen simulator demonstrates the orchestration contract.

## Deployment contract

1. Verify user, GUI session, Homebrew and Git.
2. Acquire an exclusive directory lock outside the checkout.
3. Unload the registered worker.
4. Copy explicitly configured legacy state without overwriting existing state.
5. Check out the requested revision and install Python dependencies.
6. Render the launcher, optional environment, LaunchAgent and rotation files.
7. Run preflight (advisory by default), release the lock, and start the worker.

Every successful deployment deliberately restarts the worker. This is repeatable
but not a zero-change Ansible run. A failed deployment leaves an unloaded worker
stopped; correct the error and rerun. Source files are never force-reset by this
role. Deploy into a dedicated checkout, not the controller checkout or a developer
worktree. Manual workers must be stopped before deployment.

The launcher is installed outside Git and does not pull at startup. This ensures
the revision tested by CI is the revision started after a crash or reboot.
Set automation_revision to a full reviewed SHA for reproducibility and rollback.
The default main is convenient for exploration only. The bundled simulator has
no runtime third-party dependencies; its build backend is pinned separately.

The existing virtual environment is reused. Changing Python minor versions
requires recreating it during a maintenance window. Rollback restores source
and dependencies, not persisted state; choose state-compatible revisions.
An interrupted controller can leave deploy.lock behind; verify no deployment is
active before removing that empty directory with rmdir.

## Private configuration and reuse

A private consumer can check out a reviewed SHA of this public repository, then
set ANSIBLE_ROLES_PATH to that checkout's deployment/ansible/roles directory.
Its own playbook uses role worker and supplies only private values:

```yaml
- name: Deploy private worker
  hosts: automation
  roles:
    - role: worker
      vars:
        automation_repo_url: "{{ private_repo_url }}"
        automation_revision: "{{ approved_commit }}"
        automation_arguments: ["{{ automation_repo_dir }}/main.py"]
        automation_requirements: requirements-runtime.txt
        automation_optional_packages: [android-platform-tools, tesseract]
        automation_environment:
          APP_DATA_DIR: "{{ automation_data_dir }}"
```

Keep private inventory, app assets, state mappings and credentials in the private
consumer. Pin the PUBLIC role checkout and PRIVATE application revision
independently. Review role updates before promoting them. No public workflow
should target a production runner.

Optional migration example:

```yaml
automation_migrations:
  - src: /absolute/old/location/state.json
    dest: workflow_state.json
```

Migration copies; it does not delete old files or replace an existing external
copy. Large historical screenshots and logs are not migrated automatically.

## Secrets

An empty automation_secrets dictionary preserves worker.env. A non-empty
dictionary renders the complete file with permissions 0600 and shell-quoted
values. Include every credential to retain; deployment settings go in
automation_environment. The launcher applies deployment settings after loading
worker.env. Vault encrypts the controller file; worker.env is plaintext with
restricted permissions on the target.

```bash
cp deployment/ansible/vault.example.yaml vault.yaml
# Edit the placeholder, then:
.ansible-venv/bin/ansible-vault encrypt vault.yaml
.ansible-venv/bin/ansible-playbook -i deployment/ansible/inventory.example.ini deployment/ansible/playbook.yaml -e @vault.yaml --ask-vault-pass
```

For unattended deployments supply --vault-password-file pointing to a protected
controller-local file or a password-client script. Neither belongs in launchd
configuration or version control. A local password file is also accessible to
code running as that user; never let untrusted CI execute on the production host.

## CI/CD example

workflows/deploy-macos.yaml.example is deliberately inactive. Copy and adapt it
in a trusted PRIVATE repository. It runs tests on a hosted runner, resolves the
requested revision to a SHA, then deploys that SHA on a Mac runner labelled
automation-deploy. Run registration under the GUI user with the runner checkout
separate from the application's deployment checkout.

It starts with manual dispatch and disallows concurrent deployments. To enable
automatic shipping, add a main push trigger, use github.sha for push checkouts,
and retain the verify-job dependency. Do not add pull_request deployment triggers.
The example needs repository read access on the target for the deployment clone.

Public CI runs only on GitHub-hosted runners. It validates Ansible syntax/lint,
template rendering, shell quoting, and the simulator on Linux, macOS and Windows.
It never deploys to production.

## Operations

```bash
launchctl print gui/$(id -u)/org.example.mobile-automation
tail -n 20 "$HOME/Library/Application Support/MobileAutomation/logs/worker.stdout.log"
launchctl bootout gui/$(id -u)/org.example.mobile-automation
```

A non-zero exit is restarted with a 60-second throttle. Successful exit is not
restarted. Registration is not proof of game-loop health. stdout/stderr are
checked hourly by a second agent and rotated above 10 MB with seven compressed
archives. copytruncate can lose a small amount of output during rotation.
The worker's SIGTERM handler wakes its wait so service stops are prompt.

To disable login startup, boot out the worker and rotation agent, then remove
their specific plist files from ~/Library/LaunchAgents. Preserve external state.

## References

- [Ansible role reuse](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_reuse_roles.html)
- [Homebrew logrotate](https://formulae.brew.sh/formula/logrotate)
- [GitHub self-hosted runner setup](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners)
