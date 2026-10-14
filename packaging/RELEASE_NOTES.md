## AutoTyper Pro 3.0.0

Desktop tools for typing, Mouse Jiggler / Anti-AFK and explicit local macro recording.

### What is new

- Language selection, persistent dark/light/system appearance and notification preferences.
- Recommended Gentle, Balanced and Keyboard-only presets; adjustable activity distance, direction, duration and keyboard shortcuts.
- Saved typing and activity profiles with rename, duplication and validated JSON import/export.
- Independent mouse movement, click, physical-key and scroll capture; local macro library and path preview.
- Playback speed, start delay, repeat count, pause between repeats and explicit display remapping.
- Persistent Stop / Escape controls, mutually exclusive typing/recording/playback and Anti-AFK yielding.
- Native macOS event monitoring avoids background keyboard-layout queries that crash on macOS 27.
- Explicit permission requests from the running app; restart preserves editor text and settings.

### Installation

Mac: choose arm64 for Apple Silicon or x64 for Intel, open the DMG, drag the app into Applications, eject the image and open the installed copy. Enable the current app under Privacy & Security → Accessibility / Device Control and Data Access. Earlier ad-hoc permission records may not cover a replacement build.

Windows: use the per-user Setup installer or extract the complete portable ZIP. No activity starts automatically. Input into elevated applications may require matching privileges.

Keyboard recording can contain sensitive input. Capture categories are individually selectable and movement-only recording is selected initially. Macros and profiles stay local. Physical-key recordings can only be replayed on their recording OS and depend on keyboard layout; preview display mapping before playback.

Packages are not Developer ID notarized or Authenticode signed. Checksums and actual platform build verification accompany published assets. The 3.0 release is published only after fresh packages and required platform checks succeed.

### Build verification

All four installers/archives use source commit `0eb3ccf254d5f1d476547bfda8a2ce1b5c6d681c`.

- macOS Apple Silicon: local build, 65 unit tests, UI smoke, native Unicode/Escape/mouse and macro capture/replay checks; packaged launch and DMG integrity verified.
- macOS Intel: built and launch-tested under Rosetta; 65 unit tests, UI smoke, bundle metadata/signature and DMG integrity verified. A physical Intel Mac was not used.
- Windows x64: local Python 3.13 build, 65 unit tests, UI/native input/macro checks; installer installation, packaged launch, uninstall and portable extraction/launch verified. Full native/UI checks ran against source; packaged checks cover launch.

See `BUILD-VERIFICATION-macos.json`, `BUILD-VERIFICATION-windows.json` and the matching SHA256SUMS files for build details and artifact hashes. These packages were built locally; GitHub Actions was unavailable due to the account billing lock.
