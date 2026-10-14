# Installation and troubleshooting

## macOS

Choose the arm64 DMG for an Apple Silicon Mac or x64 for an Intel Mac. Find the processor under **Apple menu → About This Mac**. Open the disk image, drag AutoTyperPro onto Applications, then eject the image. Open `/Applications/AutoTyperPro.app`; avoid launching a copy from the mounted image.

The current release is ad-hoc signed, without Developer ID notarization. macOS may require you to review the app under **System Settings → Privacy & Security** before opening it. Do not disable Gatekeeper or System Integrity Protection.

### macOS permissions

Enable the installed application under **System Settings → Privacy & Security → Accessibility**, called **Device Control and Data Access** on newer macOS versions. If the app is absent, use **+** to select `/Applications/AutoTyperPro.app`.

If permission appears enabled but the app still reports denial:

1. Check that you are opening the same installed copy that you granted access to.
2. Stop any active tools and use the application's Restart action. It preserves the current editor text and settings.
3. If a previous build is still registered, remove only its AutoTyperPro entry and add the current installed copy, then relaunch.

Ad-hoc signed builds have different code identities after rebuilding. An earlier grant may not apply to the replacement. The application always checks the operating system's actual result; an enabled switch for another copy is insufficient.

Version 3.0 explicitly requests permission from the running process when you choose the permission action. Its native macOS ESC listener avoids the background keyboard-layout query that caused crashes on macOS 27. If you are using 2.1.0, install the current release to receive these fixes.

## Windows

The Setup installer installs for the current user, creates an uninstaller and offers an optional desktop shortcut. For the portable edition, extract the complete ZIP and launch `AutoTyperPro.exe` inside its application folder; keep its supporting files together.

Packages target x64 Windows 10/11. They are not Authenticode signed, so SmartScreen may ask you to review the publisher. Native input can be rejected by a target running with higher privileges. Prefer ordinary, non-elevated target applications.

## Verify a download

Download the matching SHA256SUMS file from the same release. Compare the hash for the exact filename:

```bash
shasum -a 256 AutoTyperPro-3.0.0-macos-arm64.dmg
```

```powershell
Get-FileHash .\AutoTyperPro-3.0.0-windows-x64-setup.exe -Algorithm SHA256
```

A checksum detects a corrupted or mismatched download; it is not a substitute for publisher signing. Build verification is included in the release's `BUILD-VERIFICATION-macos.json` and `BUILD-VERIFICATION-windows.json` files.

## Report a problem

Include the version, OS version, processor, package filename, permission state and exact steps. For source execution, also include Python version. Do not attach private editor text, recordings, credentials or complete unredacted crash reports.
