# Contributing to AutoTyper Pro

Open an issue for a bug or a proposed change. Keep pull requests focused and describe the visible behavior, the reason for the change and how you verified it. Use English for code documentation, issues and pull requests.

## Setup

Use Python 3.11+ with Tk support. Create a virtual environment and install `requirements.txt`. On macOS the `run_mac.command` launcher also handles setup. Run `auto_typer.py` from your environment.

## Validation

```bash
python -m unittest discover -s tests -v
python tools/check_translations.py
```

These checks do not open application windows, send input or play audio. When another task is active on the desktop, keep application launches and native tests for a separate interactive test session.

On Windows, source UI checks can run on an invisible, temporary Win32 desktop:

```powershell
python tools/windows_isolated_ui.py --test ui
python tools/windows_isolated_ui.py --test entrypoint
python tools/windows_isolated_ui.py --test compact
```

The runner launches its own child process on the private desktop, checks that it is not the input desktop, and leaves the visible desktop unchanged. Automation, tray, audio and browser operations are simulated. Compact checks cover small windows, theme/scale combinations, action visibility and report drafts. This does not replace native tray/input, sound playback or packaged-launch checks. Do not run the internal child mode directly.

When the interactive desktop is available, `python tools/ui_smoke.py` exercises the source UI and native quick-access adapter.

The UI smoke test uses a simulated backend. Native integration tests send real events to their own controlled test window and require an interactive desktop. Run them only deliberately:

- macOS: install optional test dependency `pyobjc-framework-Cocoa`, then run `python tools/native_smoke.py` and `python tools/native_macro_smoke.py`
- Windows: `python tools/windows_native_smoke.py` and `python tools/windows_macro_smoke.py`

Do not change focus during native tests. Native input permission must be granted by the user. Test cancellations, ESC, denied permission and teardown when changing input code. Keep all Tk mutations on the UI thread; workers communicate through queues and synchronization primitives.

## Build

- macOS app: `./make_executable_mac.sh`
- macOS DMG: install `ds-store` and `mac-alias`, then run `python packaging/macos/build_dmg.py` after the app build.
- Windows app: `make_executable.bat`
- Windows Setup: Inno Setup 6 with `packaging/windows/installer.iss` after the app build; pass `/DAppVersion=<VERSION>` using the value from `preferences.py`.

The release workflow builds macOS arm64, macOS x64 and Windows x64, validates packaged launch and checks Windows install/uninstall before publication. Do not label an existing binary with a new version after changing runtime code. Generated artifacts, virtual environments and local preferences must remain outside Git.

## Project layout

| Path | Purpose |
| --- | --- |
| `auto_typer.py`, `activity_page.py`, `macro_page.py`, `onboarding.py` | Desktop UI and introduction |
| `engine.py` | Validated configurations and cancellable workers |
| `platform_backend.py` | Native macOS/Windows input and permissions |
| `preferences.py`, `profiles.py`, `localization.py`, `locales/` | Local settings, saved profiles, translations and version |
| `macros.py`, `macro_recorder.py`, `event_capture.py` | Validated recording, playback and platform capture |
| `tests/`, `tools/` | Regression checks, native checks and asset tooling |
| `assets/`, `sounds/` | Bundled application resources |
| `packaging/`, `.github/workflows/` | Installers and release automation |

The repository currently has no license file. Do not assume it grants redistribution rights or introduce a license without the owner's decision.

## Translations

Help make AutoTyper Pro accessible in your language. See [Translating](docs/TRANSLATING.md) for partial catalogs, validation and contributor credits.
