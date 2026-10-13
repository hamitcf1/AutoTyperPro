<p align="center"><img src="assets/icon.png" width="88" alt="AutoTyper Pro icon"></p>
<h1 align="center">AutoTyper Pro</h1>
<p align="center"><strong>Less repetition. Your pace. Your control.</strong><br>Automatic typing and Mouse Jiggler / Anti-AFK for macOS and Windows.</p>
<p align="center"><a href="https://github.com/hamitcf1/AutoTyperPro/releases/latest">Download</a> · <a href="docs/INSTALLATION.md">Installation & permissions</a> · <a href="CONTRIBUTING.md">Contribute</a> · <a href="README_TR.md">Türkçe</a></p>

![AutoTyper Pro overview](docs/assets/overview.svg)

AutoTyper Pro is a local desktop utility for repetitive typing and small, idle-triggered mouse movements. Paste your text, choose a rhythm, and switch to the target application during the countdown. Start Mouse Jiggler independently when you need it. **Escape stops both tools.**

No account. No telemetry. No automatic activity on launch.

## Download

| Platform | Recommended download | Alternative |
| --- | --- | --- |
| macOS — Apple Silicon | [Drag-to-install DMG](https://github.com/hamitcf1/AutoTyperPro/releases/download/v2.1.0/AutoTyperPro-2.1.0-macos-arm64.dmg) | M-series Macs |
| macOS — Intel | [Drag-to-install DMG](https://github.com/hamitcf1/AutoTyperPro/releases/download/v2.1.0/AutoTyperPro-2.1.0-macos-x64.dmg) | Intel Macs |
| Windows — x64 | [Setup installer](https://github.com/hamitcf1/AutoTyperPro/releases/download/v2.1.0/AutoTyperPro-2.1.0-windows-x64-setup.exe) | [Portable ZIP](https://github.com/hamitcf1/AutoTyperPro/releases/download/v2.1.0/AutoTyperPro-2.1.0-windows-x64-portable.zip) |

[All releases, SHA-256 checksums and build verification](https://github.com/hamitcf1/AutoTyperPro/releases/latest)

**Release status:** the downloadable version is **2.1.0**, whose application interface is Turkish. The repository documentation is English-first. The main branch additionally fixes explicit macOS permission requests and a macOS 27 ESC-listener crash; these fixes are not included in the 2.1.0 downloads yet. English/Turkish language selection, custom activity profiles and macro recording are [proposed for the next major version](docs/global-product-design.md).

Packages are not Developer ID notarized or Windows Authenticode signed. See the [installation guide](docs/INSTALLATION.md) before opening them.

## What you can do today

| Auto Typer | Mouse Jiggler / Anti-AFK |
| --- | --- |
| Six speed modes, including a custom random range | Independent start and stop controls |
| Start delay from 0 to 60 seconds | Adjustable idle threshold and activity interval |
| Natural timing variation and word pauses | Small cursor movement with return to the original position |
| Newlines as spaces, Shift+Enter or skipped | Optional F18 key activity, off by default |
| Unicode typing, live progress and time estimate | Automatically waits while Auto Typer runs |
| Optional sound notifications | Avoids restoring the cursor over a user's mouse movement |

Mouse Jiggler does not click. It does not guarantee that a particular service will show you as online or that the operating system will stay awake.

## Quick start

1. Download the package matching your platform.
2. **Mac:** open the DMG, drag AutoTyperPro into Applications, eject the image, then open the installed app. **Windows:** run Setup, or extract the entire portable ZIP before launching.
3. On macOS, grant the installed app keyboard/mouse control access when requested. See [permissions troubleshooting](docs/INSTALLATION.md#macos-permissions).
4. Paste text, choose your settings and start typing. Switch to your target app during the countdown.
5. Use the separate Mouse Jiggler tab for idle-triggered activity. Press **Escape** to stop.

A short, skippable introduction appears on first launch and can be replayed from the application.

## Privacy and control

Text and input activity stay on your device. The application does not send them to a server. Typing and mouse activity start only when you choose to start them and stop when the application closes. The permission restart action uses a temporary local file to restore your current text/settings and deletes its owned file after restoration.

## Run from source

Requires Python 3.11+ with Tk support. Packaged downloads include their runtime; Python is only needed for source development.

```bash
git clone https://github.com/hamitcf1/AutoTyperPro.git
cd AutoTyperPro
python -m venv .venv
```

**macOS:** `./run_mac.command` installs dependencies and launches the app. **Windows:** run the following in PowerShell:

```powershell
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python auto_typer.py
```

Source execution may require permission for Python or the launching terminal rather than the packaged application.

## Development

See [Contributing](CONTRIBUTING.md) for tests, native input verification and build commands. Build sources for the macOS DMG and Windows installer are kept in `packaging/`; generated binaries and virtual environments are excluded from Git.

Found a problem? [Report a bug](https://github.com/hamitcf1/AutoTyperPro/issues/new?template=bug_report.yml) with the application version, OS, installation method and reproduction steps. Please remove private text and identifying details from logs or screenshots.
