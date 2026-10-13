# macOS redesign implementation plan

Goal: Deliver the approved desktop redesign and independent Mouse Jiggler.
Architecture: Retain CustomTkinter; extract validated configuration and cancellable workers into engine.py, use native macOS events through platform_backend.py, and queue UI updates on the Tk main thread.
Spec: ../specs/2026-10-13-macos-redesign.md
Execution: Inline, as requested by the user. Existing clean clone is the workspace; feature branch isolates implementation.

## Tasks
- [x] 1. Write failing engine tests for Unicode/newlines, invalid inputs, cancellation, errors, jiggler scheduling and typing coordination; implement engine.py and run unittest.
- [x] 2. Implement platform_backend.py with permission checks, Unicode injection, idle detection, bounded cursor excursion and optional F18. Verify native API calls without unsolicited events.
- [x] 3. Redesign auto_typer.py with two Turkish views, queue polling, persistent status, validation and coordinated shutdown. Launch and inspect UI.
- [x] 4. Update launch/build scripts, requirements, icon and documentation. Build and launch the app; test typing in controlled target if permission allows.
- [ ] 5. Review, run full verification, commit and push.

Review focus: Nonfinite numeric inputs; cancel during countdown; close while worker active; permission denial; mouse movement by user during excursion.

## Execution evidence — 2026-10-13
- 21 unit tests pass, including live countdown cancellation, permission denial, inherited modifier clearing, missing/failed ESC listener and cursor-user interference.
- tools/ui_smoke.py passes real CTk navigation, minimum 980 × 740 size, typing, invalid/empty input, random mode, jiggler coordination, ESC and shutdown with a fake event backend.
- tools/native_smoke.py passes native Turkish Unicode, emoji, Shift+Enter, global ESC and cursor return in its own foreground test window.
- PyInstaller 6.22.3 builds version 2.0.0 on arm64 Python 3.14. codesign --verify --deep --strict passes. Application launched and inspected; installed at ~/Applications/AutoTyperPro.app.
- Packaged Accessibility permission is not granted. The app displays the permission banner and blocks activity until the user grants access. Packaged event injection therefore remains unverified; the same native backend was verified from source.
- Independent final reviewer raised listener startup/health and stale-environment dependency repair. Both addressed with regression tests / launcher update.
- Ruling: use 1120 × 800 default size and scrollable settings panels to keep controls accessible at minimum size and when the permission banner is displayed.
- Ruling: keep Windows adapter/build support but report it unverified on this Mac.
