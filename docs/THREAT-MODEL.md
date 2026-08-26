# Threat model

Last reviewed: 26 August 2026

## Security objectives

1. Microphone audio is transient and bounded unless the user deliberately
   chooses a transcription mode and starts capture.
2. The active provider boundary is visible before and during a session.
3. Credentials, raw audio, and transcript content do not enter diagnostics or
   application logs.
4. Text persistence is opt-in or an explicit export, privately permissioned,
   bounded by retention, and deletable.
5. Release origin, dependency composition, and test evidence are independently
   inspectable.

## Assets and trust boundaries

| Asset | Boundary | Primary controls |
| --- | --- | --- |
| Microphone frames/segments | PortAudio process memory | Explicit Start/Stop, bounded queues, local VAD, no audio-file API |
| Groq key | Environment/`.env` or owner-only config to HTTPS header | No value in UI diagnostics/logs, environment precedence, normalized errors |
| Transcript/history/export | GTK memory to user-selected local storage | History off by default, `0600` files, retention/delete, export confirmation |
| Provider response | Groq HTTPS or local child process | Minimal response parsing, bounded sizes/timeouts, normalized errors |
| Local model/runtime | User-selected executable/files | Feature flag, source only, path validation, active-process termination |
| Release artifact | GitHub Actions to GitHub Release | Version checks, checksum, SBOM, provenance attestation |

## Threats and mitigations

| Threat | Mitigation | Residual risk / limit |
| --- | --- | --- |
| Accidental continuous recording | Foreground session state, explicit Start/Stop, stop cleanup, no background service | Desktop/audio stack may expose microphone indicators differently |
| Unbounded audio/request memory | Fixed capture queue, bounded provider semaphores, max segment/audio size | Oldest capture frames can be dropped under severe load |
| Secret in exceptions or diagnostics | Response bodies discarded, provider errors normalized, presence-only doctor fields, regression tests | External shell/desktop logs and a user-edited `.env` are outside app control |
| Transcript/audio in logs | No content logging; local stderr discarded; state tracker stores status only | A modified dependency/runtime may log independently |
| Local user reads saved text/key | `0700` directories and `0600` files where supported | Same-user malware/root, backups, and filesystems ignoring POSIX modes remain trusted |
| Network interception | HTTPS provider endpoint and no custom certificate bypass | Provider/cloud/account compromise is outside the app boundary |
| Provider retains customer data | Visible cloud consent and current vendor-policy links | Provider policy/controls can change; user must review account settings |
| Malicious local whisper binary | Explicit feature flag, user selection, disabled in Flatpak, no automatic download | Selected code has user-session authority and can exfiltrate received speech |
| Path/symlink archive attack in benchmark | Checksum pin and traversal/link/device rejection before extraction | Corpus download host and checksum publication remain supply-chain dependencies |
| Dependency/release tampering | Pinned Flatpak sources, dependency audit, CodeQL/Bandit, checksum, SBOM, GitHub attestation | These prove origin/composition, not absence of vulnerabilities |
| Stale or unexpected history schema | Unknown schema fails closed; atomic replacement and deletion tests | Disk failure can prevent save/delete and is reported to the user |

## Out of scope

- A compromised kernel, root account, desktop compositor, audio server, Python
  interpreter, clipboard manager, filesystem, or physical device.
- Privacy/security behavior of third-party binaries, models, Groq, GitHub,
  distribution runtimes, backups, or downstream apps beyond documented calls.
- Hiding transcript text from someone who can see the unlocked desktop window.
- Guaranteeing secure erasure on SSDs, copy-on-write filesystems, snapshots, or
  backups after a file is deleted.

## Review triggers

Update this model when microphone lifecycle, provider endpoints, credentials,
history/export behavior, logging, sandbox permissions, model download, crash
reporting, analytics, package format, or release automation changes. Every
release note must state whether any of these privacy boundaries changed.
