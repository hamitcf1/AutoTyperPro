# AutoTyper Pro — macOS redesign

## Outcome
Modernize the existing Python/CustomTkinter desktop application, preserve its typing capabilities, and deliver a working Apple Silicon macOS application. Add Mouse Jiggler as a separate feature in the same application. Commit and push reviewed, verified changes to the existing GitHub repository.

## Visual design
Use a warm graphite background, layered charcoal surfaces, muted green primary actions, and macOS system typography. Establish a spacious 1100 × 760 default window with a usable minimum size. Use a restrained top navigation for Auto Typer and Mouse Jiggler, a large page title, short descriptive copy, and a persistent status area. Avoid the current stack of cramped radio buttons and disconnected panels.

The Auto Typer view places the editor and its clipboard actions on the left, with speed and behavior settings on the right. Character count, word count, estimated duration, countdown, and progress have clear hierarchy. Start and Stop remain visible. Include deliberate empty, running, completed, stopped, validation-error, and permission-required states. Keep UI copy consistently Turkish for this delivery.

The Mouse Jiggler view uses the same design system, with an original cursor illustration, a clear active/inactive status, elapsed duration and movement count, and compact controls for idle threshold and movement interval. Its active state must remain discoverable when switching to Auto Typer.

## Typing behavior
Preserve six speed modes (30, 60, 100, 150, 250 milliseconds and random), configurable start delay, natural variation, word pauses, three newline modes, clipboard actions, progress, and optional sounds. Validate finite numeric inputs and sensible bounds before starting. Snapshot input and configuration before launching a worker. Workers communicate through a queue; all Tk operations run on the main thread. Cancellation interrupts countdown and character delays. Prevent overlapping runs and shut down workers/listeners on exit.

Separate testable typing/configuration logic from platform event injection and the interface. Replace Windows-only startup imports and the incompatible keyboard backend with a macOS-compatible event backend that supports Unicode text, including Turkish characters. Preserve Windows support where feasible through a platform adapter. Keep the existing CustomTkinter framework.

## Mouse Jiggler behavior
Default idle threshold: 60 seconds. Default activity interval: 30 seconds. Allow thresholds from 5 to 3600 seconds and intervals from 5 to 3600 seconds. Require explicit Start; never auto-start on launch. After the idle threshold is exceeded, move the pointer by approximately one point and return after approximately 80 milliseconds. Bound movement to the display and avoid returning the cursor if the user moves it during the excursion. Suspend jiggling while typing is running. Stop interrupts waiting promptly.

Offer optional F18 activity, disabled by default, matching the supplied example without assuming every target application ignores F18. Do not click, modify SSH configuration, or install a background service. ESC stops both features. Closing the app stops both features. Read user-input idle time using the macOS event API; handle synthetic activity and interval timing explicitly so movements do not accidentally trigger on every poll.

## macOS integration
Detect Accessibility permission before event injection, explain its purpose in Turkish, and provide an action opening the corresponding System Settings pane. Do not silently report successful typing or movement when permission is missing. Permission grants remain a user action in macOS. Play bundled sounds using the platform sound facility. Make asset paths work from source and the packaged app.

Provide a reliable source launcher and reproducible PyInstaller build script for the Python version available on this Mac. Package sounds and CustomTkinter resources. Generate an application icon consistent with the visual design. Install the verified app locally without overwriting an unrelated existing application. Document source execution, packaging, permissions, and limitations in Turkish and English.

## Verification and delivery
Exercise validation, Unicode/newline handling, cancellation during countdown and typing, progress/completion, worker error propagation, jiggler idle timing, stop behavior, and coordination through meaningful automated tests with fake event backends. Launch the actual UI and inspect both screens at the default and minimum window sizes. Build and launch the macOS app. Verify event injection in a controlled local text target when Accessibility access permits; otherwise report the precise unverified behavior and required user action. Inspect the final diff, commit the changes, and push to GitHub. Exclude virtual environments and build outputs from Git.

## Scope limits
No framework migration, cloud service, login, telemetry, launch-at-login daemon, or SSH changes. The app operates locally and only emits events while explicitly enabled. OS permission and signing limitations must be described accurately.
