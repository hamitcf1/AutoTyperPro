## AutoTyper Pro 2.1.0

A local desktop toolkit for automatic typing and idle-triggered mouse activity, with a redesigned Turkish interface.

### Downloads
- **Apple Silicon Mac (M1/M2/M3/M4/M5):** `AutoTyperPro-2.1.0-macos-arm64.dmg`
- **Intel Mac:** `AutoTyperPro-2.1.0-macos-x64.dmg`
- **Windows 10/11 x64 installer:** `AutoTyperPro-2.1.0-windows-x64-setup.exe`
- **Windows portable:** `AutoTyperPro-2.1.0-windows-x64-portable.zip` — extract the entire folder before launching.

### Changes
- Branded drag-to-install Mac disk images, with an Applications shortcut.
- Per-user Windows installer with Start Menu shortcut, optional desktop shortcut and uninstaller.
- Original keystroke/motion icon, plus a short, skippable first-run introduction.
- Mouse Jiggler works on both macOS and Windows; idle threshold, movement interval, optional F18 and global ESC.
- Live permission refresh and a restart action that preserves the current text/settings. No automatic reopening of System Settings.
- Native macOS Unicode typing, including Turkish characters and emoji; six speed modes and three newline behaviors.

### Installation and permissions
**Mac:** Mount the DMG, drag AutoTyperPro to Applications, eject the image, and open the installed copy. Enable it under System Settings → Privacy & Security → Accessibility (Device Control and Data Access on newer macOS). If permission is already enabled but not recognized, use **Yeniden başlat**. If an older unsigned build is still registered, remove that entry and add the current installed copy.

**Windows:** Run the installer or extract the portable ZIP. It installs for the current user without requiring administrator privileges. Typing into elevated/admin applications may require matching privileges.

These packages are not Developer ID notarized or Windows Authenticode signed. Gatekeeper/SmartScreen may ask for user approval. No security settings are changed by the installer. The application never starts typing or jiggling automatically. Text stays on your device; no account or telemetry.

SHA-256 checksum files are included for download verification. The Apple Silicon package was built on macOS 15; the Intel package was built and verified as x86_64 under Rosetta. Windows packages target x64 Windows 10/11. Build provenance and verification are recorded in `BUILD-VERIFICATION.json`. Other architectures are not included.
