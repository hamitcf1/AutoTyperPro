# Contributing to AutoTyper Pro

Open an issue for a bug or a proposed change. Keep pull requests focused and describe the visible behavior, the reason for the change and how you verified it. Use English for code documentation, issues and pull requests.

## Setup

Use Python 3.11+ with Tk support. Create a virtual environment and install `requirements.txt`. On macOS the `run_mac.command` launcher also handles setup. Run `auto_typer.py` from your environment.

## Validation

```bash
python -m unittest discover -s tests -v
python tools/ui_smoke.py
```

The UI smoke test uses a simulated backend. Native integration tests send real events to their own controlled test window and require an interactive desktop. Run them only deliberately:

- macOS: `python tools/native_smoke.py`
- Windows: `python tools/windows_native_smoke.py`

Do not change focus during native tests. Native input permission must be granted by the user. Test cancellations, ESC, denied permission and teardown when changing input code. Keep all Tk mutations on the UI thread; workers communicate through queues and synchronization primitives.

## Build

- macOS app: `./make_executable_mac.sh`
- macOS DMG: install `ds-store` and `mac-alias`, then run `python packaging/macos/build_dmg.py` after the app build.
- Windows app: `make_executable.bat`
- Windows Setup: Inno Setup 6 with `packaging/windows/installer.iss` after the app build.

The release workflow builds macOS arm64, macOS x64 and Windows x64, validates packaged launch and checks Windows install/uninstall before publication. Do not label an existing binary with a new version after changing runtime code. Generated artifacts, virtual environments and local preferences must remain outside Git.

## Project layout

| Path | Purpose |
| --- | --- |
| `auto_typer.py`, `onboarding.py` | Desktop UI and introduction |
| `engine.py` | Validated configurations and cancellable workers |
| `platform_backend.py` | Native macOS/Windows input and permissions |
| `preferences.py` | Local preferences and application version |
| `tests/`, `tools/` | Regression checks, native checks and asset tooling |
| `assets/`, `sounds/` | Bundled application resources |
| `packaging/`, `.github/workflows/` | Installers and release automation |

The repository currently has no license file. Do not assume it grants redistribution rights or introduce a license without the owner's decision.
