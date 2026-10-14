## AutoTyper Pro 3.0.1

### macOS Screen Sharing fix

Typing into another Mac through Screen Sharing now sends real keyboard gestures instead of repeating the A key. Local Unicode typing retains its existing behavior.

- Captures the current keyboard layout on the main thread, including Shift, Option and supported dead-key combinations.
- Checks the complete text before sending; unsupported remote characters show a clear error without partial input.
- Stops when the selected remote client loses focus and releases held keys on cancellation or failure.
- Verified against a real remote Mac with Latin and Turkish letters, punctuation and Shift+Enter.

Use matching keyboard layouts on both computers. Emoji and characters unavailable in the active physical layout require the remote client's clipboard paste feature. No clipboard settings are changed automatically.

This is a macOS hotfix. Windows 3.0.0 installers remain available from the previous release. Packages use ad-hoc signing and are not Developer ID notarized. Created by Hamit Can Fındık · AetheriusCo.
