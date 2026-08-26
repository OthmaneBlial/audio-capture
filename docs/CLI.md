# Command-line contracts

The CLI provides diagnostics and overrides without opening the GTK window.
Machine-readable fields are versioned so support tooling can fail closed when a
future schema changes.

## Exit codes

| Command | `0` | `1` | `2` |
| --- | --- | --- | --- |
| `--check-config` | Active provider is configured | Not used | Groq key or experimental local flag/files are incomplete |
| `--list-devices` | Discovery ran, including an empty result | Native dependency or PortAudio discovery failure | Invalid arguments |
| `--doctor` | Required readiness checks pass | One or more required checks fail | Invalid arguments |
| GUI launch | Window exited normally | GTK import or runtime startup failure | Invalid arguments |

`argparse` may use exit code `2` for any invalid option combination.

## `--list-devices --json`

The result is a JSON array. Each item has:

```json
{
  "index": 2,
  "name": "USB microphone",
  "max_input_channels": 1,
  "is_default": true
}
```

This command opens PortAudio only for discovery, closes it before returning,
does not start a stream, and does not contact a transcription provider.

## `--doctor --json`

Schema version `1` returns:

- `schema_version`: integer contract version;
- `app_version`: application version;
- `ready`: whether all required checks pass;
- `provider_probe_requested`: whether network/key verification was requested;
- `checks`: platform, desktop session, GTK, microphones, selected microphone,
  configuration, and provider results;
- `next_actions`: deduplicated safe remediation steps.

Each check has `status` equal to `pass`, `warn`, `fail`, or `skip`, plus a
human-readable `summary`. The report includes microphone indexes but does not
include microphone names, the API key, environment values, paths, IP addresses,
or provider response bodies.

For Groq, the provider check is `skip` and `contacted` is `false` by default.
Only this explicit command transmits the configured credential to the Groq
models endpoint:

```bash
voice-transcriber --doctor --probe-provider --json
```

It never transmits audio. It reports authentication/reachability status without
printing the credential or response body. For experimental local mode, the
provider check never contacts a network endpoint: it reports only whether the
explicit feature flag, executable bit, and model file are present, without
printing their paths.

## Session-only device override

```bash
voice-transcriber --device 2
```

The override must be a non-negative integer. It takes precedence for one launch
without changing the saved device. A failed open leaves the application stopped
with an actionable error.
