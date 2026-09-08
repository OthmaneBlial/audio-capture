# Native release checklist

Record the exact commit, tag, workflow URL, archive names, checksums, tester
environment, and result for every release. A successful CI build is separate
from a downloaded-asset runtime check.

## Source gate

- [ ] Cargo package version, changelog, metadata, tag, and release title agree.
- [ ] `cargo fmt --all -- --check` passes.
- [ ] `cargo test --locked --all-targets` passes.
- [ ] `cargo clippy --locked --all-targets -- -D warnings` passes.
- [ ] `cargo deny check advisories licenses bans sources` passes.
- [ ] No credentials, recordings, transcripts, or local configuration are in
      the tree or release notes.

## Build and archive gate

- [ ] Linux x86_64 archive builds on the pinned runner.
- [ ] macOS arm64 `.app.zip` builds and contains a microphone usage description.
- [ ] Windows x86_64 archive builds on the MSVC runner.
- [ ] Every archive has the exact version/target name and a SHA-256 sidecar.
- [ ] Uploaded asset bytes match the published checksums.
- [ ] Release notes state what was built and what was not runtime-tested.

## Downloaded-asset gate

- [ ] Each available target extracts on a clean profile.
- [ ] `--version`, `--doctor --json`, and `--list-devices --json` work there.
- [ ] `--test-microphone --json` is run where a microphone is available.
- [ ] Manual UI review covers ready, settings, recording, complete, and error
      states with keyboard focus and visible checkbox states.
- [ ] One tester-owned Groq transcript/translation request succeeds, or the
      release notes explicitly leave that gate open.

## Public presentation gate

- [ ] README install commands point to the current release assets.
- [ ] Screenshots show the actual native application and contain no private text.
- [ ] The support matrix distinguishes CI evidence from real-device evidence.
- [ ] The final demonstration video is captured only after all earlier gates.
