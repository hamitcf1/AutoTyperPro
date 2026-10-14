# AutoTyper Pro 3.0 — global product design

Status: approved design. Source implementation is complete; cross-platform release verification is tracked separately. The published 2.1 release does not contain these features.

## Purpose and scope

Make AutoTyper Pro a polished desktop utility that international users can discover, download, install and configure without reading development history. Keep macOS Apple Silicon, macOS Intel and Windows x64 support in one application. Retain the existing Python/native input architecture rather than maintain separate applications.

The owner requested a professional repository, reliable installers, English application copy, language settings, highly customizable Mouse Jiggler / Anti-AFK activity, recommended defaults and recorded actions. The proposed interpretation of recorded actions includes mouse movement, clicks and physical keyboard keys, with separate capture switches and movement-only capture selected initially.

## Product experience

Four clear destinations: Auto Typer, Anti-AFK, Macros and Settings. Show active tool, recording/countdown state and a persistent Stop control. Keep the graphite and sage identity, refine the existing icon at small sizes, and use consistent typography, spacing and keyboard focus. Advanced options appear below recommended settings rather than overwhelm the initial view. Minimum supported window remains usable with scrolling.

English is the default language regardless of system locale. Turkish is selectable in Settings and saved locally. All user-visible labels, status messages, validation errors, onboarding and permission guidance use stable localization keys. Stored settings use stable identifiers rather than translated labels. Language changes are permitted when idle and preserve editor contents and configuration.

Settings include language, dark/light/system appearance, sound notifications and onboarding replay. No automatic activity on launch. Only explicit saved profiles and settings persist; editor drafts are not saved by default.

## Mouse Jiggler / Anti-AFK

Use both names in the page heading and documentation. Recommended preset **Gentle**: wait for 60 seconds of inactivity, minimum interval 30 seconds, one macOS point/Windows pixel out-and-back movement, keyboard activity off. **Balanced**: 60-second inactivity, 60-second interval, four-unit movement. **Keyboard only**: 60-second inactivity, 60-second interval, F18; explicitly explain that applications may assign F18 to a shortcut. Label Gentle as Recommended and provide Restore recommended defaults.

Expose idle threshold and minimum interval (5–3600 seconds), movement distance (1–100), movement mode (off, horizontal return, vertical return, small square), excursion duration (50–1000 ms) and keyboard activity. Keyboard choices: None, F13–F20 including F18 as suggested, and Custom. Custom supports a single supported physical key with optional Shift, Control, Alt/Option and Command/Windows modifiers; reject Escape, unknown keys and modifier-only combinations. Release every pressed key on cancellation or error.

Saved named profiles can be created, duplicated, renamed, deleted and exported/imported as versioned JSON. Validate values before replacing the active profile. Built-in presets cannot be overwritten. Changing a live configuration requires stopping first. Display the effective configuration and distinguish unsaved changes from a saved profile.

Activity remains bounded by the current display. A user mouse move during an excursion cancels restoration. Typing or macro recording/playback pauses Anti-AFK. Resume only after the relevant idle conditions are met. Do not imply that synthetic activity guarantees a particular application's online status or system sleep behavior.

## Macros

Record only after a visible countdown (default three seconds). Capture switches control movement, clicks and keyboard separately. Show Recording continuously. Stop via ESC or the visible control; exclude the terminating ESC. Cap each recording at five minutes and 10,000 events, with explicit completion status. Coalesce mouse movement to at most 30 samples per second while preserving click/key order. Do not capture clipboard contents, screenshots or application text.

Represent events as monotonic time offsets and typed data: move coordinates, mouse-button down/up, physical key down/up and scroll deltas. Store display bounds and recording platform. Keyboard recordings are platform-specific and must not be silently replayed on another platform. Profiles containing only portable movement can be imported on either platform.

Allow a macro to be named, previewed as a path plus event summary, saved, renamed, duplicated, deleted, imported and exported. Explain that keyboard-enabled recordings may contain sensitive input before recording. No background recording, telemetry or automatic upload. Store JSON in the user's application data directory using atomic writes.

Playback has a countdown, speed multiplier (0.25–4), repeat count (1–100) and pause between repeats (0–3600 seconds). Default is one repeat at original speed. Validate the display layout before playback; offer explicit fit-to-current-primary-display mapping for movement rather than silently clicking different targets. Never replay incompatible keyboard events. Provide a preview without sending input. Out-of-bounds coordinates, malformed timing, unmatched key/button transitions and unsupported events are rejected before playback.

ESC cancels all tools. Cancellation releases held keys/buttons. Recording, typing and playback are mutually exclusive; Anti-AFK yields to them. A runtime failure stops the activity and reports a localized error. Keep Tk calls on the UI thread and transfer worker state through queues.

## Architecture

Separate localization, versioned settings/profile storage, macro validation/recording/playback and native platform adapters from page rendering. The UI consumes validated immutable configuration objects. Existing typing behavior and native Unicode injection remain intact.

On macOS, use native CoreGraphics event taps and raw physical key codes. Do not query Carbon input-source/layout APIs from background threads: the supplied macOS 27 crash report shows a dispatch assertion in that path. Distinguish input posting permission from event-listening readiness. Request accessibility access only on an explicit permission action; recheck actual OS state rather than persisting a grant flag. Permission restarts preserve text and settings.

On Windows, preserve checked SendInput results and native idle/display calculations. Recording uses platform event listeners; playback uses checked native injection. Platform code owns event handles and teardown and exposes cancellation-safe methods.

## Repository and distribution

README.md becomes the authoritative English landing page: original icon, concise description, real application screenshots, supported platforms, prominent latest-release downloads, quick start, privacy and limitations. Move Turkish documentation to README_TR.md. Remove the duplicate English README and outdated internal planning documents, machine-specific instructions and obsolete tracked environment snapshots after confirming no build dependencies reference them. Keep meaningful tests, packaging sources and reproducible asset generators.

Add CONTRIBUTING.md, issue templates and a concise build/install/troubleshooting guide. Do not invent a license: preserve an existing license or ask the owner to choose one if absent. Describe feature availability honestly; screenshots and README claims must match the shipped release.

Use one application version source for package metadata, filenames, installer scripts and release tags. CI verifies changes before release, builds all three platforms, checks application launch and Windows installation/uninstallation, then publishes checksums and release notes alongside packages. DMGs retain drag-to-Applications installation. Portable Windows ZIPs contain the complete application directory.

Public macOS signing/notarization requires a suitable Developer ID identity; a local Apple Development certificate is not equivalent. Unsigned packages are labeled accurately. Do not change OS security settings or export signing credentials. GitHub Actions availability must be checked before promising a new cross-platform release; earlier jobs were blocked by an account billing issue. Never reuse an older Windows binary under a new version label after runtime changes.

## Acceptance criteria

- English and Turkish flows include validation, permission prompts and runtime errors, with settings retained across restart.
- Recommended Anti-AFK defaults are visible, editable and restorable; custom keys and movement remain bounded and cancellation-safe.
- Profiles and macros round-trip through validated JSON; corrupt/imported files leave existing data intact.
- Recording captures only selected event categories and playback follows timing, speed and repeat controls.
- Global ESC works without keyboard-layout background calls; stop, denied permissions and shutdown release all native resources and pressed inputs.
- Controlled native targets verify Unicode, keyboard combinations, mouse movement, recording/playback and cancellation on the tested platforms.
- Installer files, version metadata, release notes and checksums agree; public download links work. Actual platform verification and signing limitations are documented.

The owner approved this design and the implementation plan. A new installer release requires the platform checks above to succeed. The shipped release remains 2.1.0 until replacement artifacts have passed their required checks.
