# Command-line contracts

The Rust binary exposes local diagnostics without opening the desktop window.
No diagnostic command sends audio or calls Groq.

## Commands and exit codes

| Command | Exit `0` | Exit `1` | Exit `2` |
| --- | --- | --- | --- |
| `--check-config` | The file parses and passes validation | Invalid/unreadable configuration | Invalid command-line arguments |
| `--list-devices` | Input discovery completed | The host cannot enumerate inputs | Invalid command-line arguments |
| `--doctor` | Configuration and input discovery completed | A required local check failed | Invalid command-line arguments |
| `--test-microphone` | A three-second stream opened without a stream error | The stream could not open or reported an error | Invalid command-line arguments |
| no flag | Desktop window exits normally | Native window startup failure | Invalid command-line arguments |

`clap` owns `--help`, `--version`, and invalid argument handling.

## `--list-devices --json`

The result is a JSON array. Each item currently contains:

```json
{
  "index": 0,
  "name": "Built-in Microphone",
  "identity": "5c3a1b9d4ef78120b6d3a10f",
  "default": true,
  "channels": 1,
  "sample_rate": 48000,
  "sample_format": "F32"
}
```

The command performs discovery only. The identity is an opaque SHA-256-derived
fingerprint of the backend identity, normalized device name, and channel count;
it detects a reused saved selection but is not a hardware UUID.

## `--doctor --json`

The current compact report contains `ok`, `config_ok`,
`provider_configured`, `input_devices`, and `version`. It intentionally does
not include API keys or environment values. A future schema version will be
added before external support tooling depends on this output.

## `--check-config --json`

The report contains `ok`, `provider_configured`, and the local configuration
path. `ok` means the file is valid; a missing key or cloud consent makes the
provider unavailable but does not make the local file invalid.

## `--test-microphone --json`

This command opens the default input for three seconds, counts the 30 ms
16-kHz frames delivered by the bounded queue, reports the maximum local signal
level, then stops the stream. It never stores the frames or sends them to a
provider. Example shape:

```json
{
  "ok": true,
  "device": "Built-in Microphone",
  "frames": 94,
  "peak_level": 0.12,
  "stream_error": null
}
```

Use it for a privacy-safe compatibility report. Do not attach recordings or
configuration files.
