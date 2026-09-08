# Threat model

Last reviewed: 8 September 2026

## Security objectives

1. Microphone audio is transient and bounded unless the user deliberately
   starts a session and accepts the configured provider boundary.
2. The active provider boundary is visible before and during a session.
3. Credentials, raw audio, and transcript content do not enter diagnostics or
   application logs.
4. Text persistence is opt-in or an explicit export, privately permissioned,
   bounded by retention, and deletable.
5. Release origin, dependency composition, and test evidence are inspectable.

## Assets and trust boundaries

| Asset | Boundary | Primary controls |
| --- | --- | --- |
| Microphone frames/segments | CPAL process memory | Explicit Start/Stop, bounded queues, local VAD, no audio-file API |
| Groq key | Environment or owner-local config to HTTPS header | No value in diagnostics/logs, environment precedence, normalized errors |
| Transcript/history/export | egui memory to user-selected local storage | History off by default, bounded retention/delete, export confirmation |
| Provider response | Groq HTTPS | Minimal parsing, bounded sizes/timeouts, normalized errors |
| Release artifact | GitHub Actions to GitHub Release | Version checks, checksums, dependency policy, least-privilege publishing |

## Threats and mitigations

| Threat | Mitigation | Residual risk / limit |
| --- | --- | --- |
| Accidental continuous recording | Foreground state, explicit Start/Stop, cleanup, no background service | Desktop/audio stack indicators are outside the app |
| Unbounded audio/request memory | Fixed capture queue, bounded provider jobs, max segment/audio size | Oldest capture frames can be dropped under severe load |
| Secret in errors or diagnostics | Discard response bodies, normalized errors, presence-only doctor fields, regression tests | Shell logs and user-edited config are outside app control |
| Transcript/audio in logs | No content logging; status-only request tracker | A modified dependency/runtime could log independently |
| Unauthorized local reads | Owner-local config/history permissions where supported | Same-user malware, root, backups, and permissive filesystems remain trusted |
| Network interception | HTTPS provider endpoint without certificate bypass | Provider/cloud/account compromise is outside the app boundary |
| Provider retention changes | Visible consent and links to current vendor policy | The project cannot enforce vendor policy |
| Release tampering | Pinned actions, dependency checks, checksums, and reviewable workflow | These controls do not prove absence of vulnerabilities |
| Stale session result | Session generation and ordered result checks | A process crash can still lose an in-memory draft |

## Out of scope

- A compromised kernel, root account, desktop compositor, audio server,
  clipboard manager, filesystem, physical device, or operating system.
- Privacy/security behavior of third-party binaries, Groq, GitHub, distribution
  runtimes, backups, or downstream apps beyond documented calls.
- Hiding transcript text from someone who can see the unlocked desktop window.
- Secure erasure guarantees on SSDs, snapshots, or backups after deletion.

## Review triggers

Update this model when microphone lifecycle, provider endpoints, credentials,
history/export behavior, logging, package format, or release automation changes.
Every release note must state whether a privacy boundary changed.
