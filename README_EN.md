# AutoTyper Pro 2.1

A local desktop toolkit with automatic typing and an independent Mouse Jiggler. The redesigned Turkish interface includes a spacious editor, graphite surfaces, live progress, and persistent activity status. Text stays on your device.

[Download macOS / Windows installers](https://github.com/hamitcf1/AutoTyperPro/releases/tag/v2.1.0)

Mac: open the DMG for your processor, drag the app to Applications, eject the image and launch the installed copy. Windows: use the per-user installer or extract the entire portable ZIP. A short skippable introduction appears once and can be replayed from the app.

## Run on macOS

On this Mac, open `~/Applications/AutoTyperPro.app`. Rebuilt bundles are available at `dist/AutoTyperPro.app`. To run from source:

```bash
./run_mac.command
```

Requires Python 3.11+ with Tk support. Developed on Apple Silicon using Python 3.14. The source launcher creates a virtual environment on first run and checks/repairs dependencies on every launch.

Enable AutoTyperPro in **System Settings → Privacy & Security → Accessibility**. Source execution may require permission for Python or the launching terminal. The permission banner opens the relevant settings. Permission status refreshes automatically. If an already granted permission is still rejected, use **Yeniden başlat** (Restart); the app preserves text/settings through a temporary local file that is deleted after restoration. Run the installed copy rather than an older build. An outdated unsigned permission record may need removal and replacement with the current installed app. Newer macOS calls this permission Device Control and Data Access. Root privileges are not required.

The local bundle is ad-hoc signed, not Developer ID signed or notarized. Distribution to other Macs may require additional Gatekeeper approval.

## Automatic typing

Paste text, select a speed, set a start delay, and click **Yazmaya başla**. Switch to the target application during the countdown. ESC stops both tools.

Six speed modes: 30, 60, 100, 150, 250 ms, or a random 10–5000 ms range. Start delay accepts 0–60 seconds. Optional natural variation, word pauses, and sound notifications are included. Newlines can become spaces, Shift+Enter, or be skipped. Native macOS events support Unicode, including Turkish characters; target applications must accept Unicode input. Estimates exclude target application processing latency.

## Mouse Jiggler

Use the separate tab and explicitly start it. Defaults: 60 seconds idle threshold, 30 seconds minimum interval. Both accept 5–3600 seconds. Once idle, it moves the cursor approximately one point and returns after approximately 80 ms. Synthetic activity can reset macOS idle time, so subsequent movement requires both the idle threshold and minimum interval.

No clicking or automatic startup. It pauses during typing and continues across tab switches. It avoids restoring the cursor if the user moves it during the excursion. Optional F18 activity defaults to off because applications may bind it to a shortcut. Stop, ESC, or closing the application ends activity. It does not guarantee system sleep prevention or presence status in other applications.

## Verify and build

```bash
.venv/bin/python -m unittest discover -s tests -v
./make_executable_mac.sh
```

Output: `dist/AutoTyperPro.app`. Sounds and CustomTkinter resources are bundled. `requirements-lock.txt` records the verified Mac environment and includes macOS-specific PyObjC packages; use `requirements.txt` on other platforms.

Mouse Jiggler supports macOS and Windows. GitHub Actions builds Mac arm64, Mac Intel and Windows x64 artifacts, checks the packaged launch and verifies Windows installation/uninstallation before publication. Packages are not notarized or Authenticode signed; Gatekeeper/SmartScreen may require approval.

Build DMGs with `python packaging/macos/build_dmg.py` after installing `ds-store` and `mac-alias`. The Windows installer uses Inno Setup 6 and `packaging/windows/installer.iss`. The **Release installers** workflow publishes only after all three platforms pass.
