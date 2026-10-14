## AutoTyper Pro 3.1.0

Desktop quick access, community translations and visible product ownership.

Created by [Hamit Can Fındık](https://github.com/hamitcf1) · [AetheriusCo](https://github.com/AetheriusCo).

### What is new

- Native macOS menu-bar utility and Windows system-tray actions for opening tools, controlling Anti-AFK, stopping all activity and quitting.
- Windows taskbar identity and application icon; optional system notifications for completion and actionable errors.
- Optional background operation when the window closes. Disabled by default; hiding never starts activity, and Quit stops all tools.
- About/support area with creator and organization links, translation credits and a user-reviewed bug report summary. Reports are submitted by the user on GitHub.
- Reviewed locale registry with partial-translation fallback, duplicate/placeholder validation, contribution guide and translation issue form.
- Refined neutral surfaces, floating rounded navigation, compact preference groups and reduced-motion introduction. Native menus follow the OS appearance; the Tk window does not use Apple's native Liquid Glass material.
- Consistent light theme across tool pages and the introduction; safe cleanup of native status items and late notification callbacks.

### Install

Mac: choose arm64 for Apple Silicon or x64 for Intel, open the DMG, drag into Applications, eject the image and open the installed app. Enable the current app's input permission in Privacy & Security. Ad-hoc replacement builds may require a renewed grant.

Windows: use Setup or extract the complete portable ZIP. The notification-area icon may initially be in Windows' hidden-icons area.

Enable system notifications and background operation separately in Settings. Notification permissions depend on the OS; denial does not prevent automation. Editor text and recorded input are never included in notifications or the generated technical summary.

Packages are not Developer ID notarized or Authenticode signed. Published assets include checksums and platform build-verification reports. Intel Mac packages are built and checked under Rosetta; no physical Intel Mac is used.

### Screen Sharing compatibility

Includes the 3.0.1 physical-key fix for macOS Screen Sharing. Use matching keyboard layouts on both computers. Unsupported remote characters are rejected before typing starts; local Unicode support is preserved.
