# Flatpak packaging research plan

## Main question

What is the smallest current, supportable Flatpak contract for packaging Voice
Transcriber as a GTK 3/Python application with microphone access, outbound
Groq requests, explicit privacy permissions, and reproducible dependencies?

## Subtopics

1. **Runtime and Python/GTK packaging:** identify the currently appropriate
   maintained GNOME runtime, official manifest conventions, and a defensible
   way to vendor Python dependencies without network access during the build.
2. **Permissions and validation:** identify the minimum official Flatpak finish
   arguments for microphone/audio-server access and networking, plus current
   Flathub validation/release expectations.

## Synthesis

The findings will become `docs/packaging/DECISION.md`, the application manifest,
generated dependency modules, CI validation, and a clean-install smoke test.
Only claims supported by primary documentation or a successful build will be
marked supported.
