# Daily dictation usability protocol

Status: recruiting. This protocol requires five real Linux participants; CI,
maintainer walkthroughs, and synthetic-audio tests do not count as sessions.

## Research question

Can a Linux user install Voice Transcriber, understand the cloud boundary,
dictate and correct one sentence, intentionally keep or discard it, and explain
what was stored without maintainer coaching?

## Participant and privacy rules

- Recruit five adults who use a Linux desktop for writing at least weekly.
- Include at least two Wayland sessions, one X11 session, one non-default
  microphone, and one participant who does not normally use developer tools.
- Ask participants to use a harmless supplied sentence. Do not collect their
  audio, API key, transcript, screen recording, shell history, or environment
  dump.
- Record only consented, anonymised observations and the exact package version,
  distribution, desktop/session, audio route, task result, and participant's
  boundary explanation.
- Stop immediately if a credential or sensitive transcript becomes visible.

## Twenty-minute script

1. Give the participant only the release URL and this prompt: “Install the app,
   then turn this sentence into text you can paste: *The green notebook is on
   the second shelf.*”
2. Observe install/checksum friction and whether `--doctor` is needed.
3. Ask them to choose the intended microphone and explain what the meter means.
4. Ask where audio goes before they accept the first-run boundary.
5. Ask them to dictate, stop confidently, correct one word, undo and redo the
   correction, then copy the result.
6. Ask them to export Markdown, identify the destination, and inspect the
   history setting without enabling it.
7. Ask them to clear the desk and explain what remains on disk.
8. Ask for one sentence each on confidence, surprise, and the biggest obstacle.

## Observation sheet

| Field | Allowed value |
| --- | --- |
| Anonymous session ID | `S01`–`S05` |
| Package/source commit | Exact release tag and SHA |
| Environment | Distribution, desktop, session, audio route, architecture |
| First copied transcript | Pass/fail and elapsed minutes |
| Microphone selection | Direct / recovered / failed |
| Start/stop confidence | Clear / hesitation / failed |
| Editing/copy/export | Pass/fail per task |
| Cloud boundary | Accurate / partial / incorrect, paraphrased only |
| Retention understanding | Accurate / partial / incorrect |
| Obstacles | Observed behaviour, no inferred motive |
| Roadmap change | Linked issue or explicit “none” |

## Publication gate

Publish `FINDINGS.md` only after all five consented sessions. Aggregate patterns;
do not publish quotes or environment combinations that could identify a person.
Every product change must link to an observation count, and contradictory
findings remain visible instead of being averaged away.
