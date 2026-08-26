# Benchmark receipts

Commit reviewed JSON receipts here only after a complete, reproducible run.

## Published local prototype receipt

[`local-tiny-en-github-runner.json`](local-tiny-en-github-runner.json) was
produced by [Actions run 33015305254](https://github.com/OthmaneBlial/audio-capture/actions/runs/33015305254),
not edited by hand.

| Field | Result |
| --- | --- |
| Corpus slice | 25 `test-clean` samples, one from each of 25 speakers |
| Reference words | 627 |
| Word errors / WER | 37 / 5.90% |
| Wall-clock latency | p50 1,043.810 ms; p95 1,508.576 ms |
| Hardware | GitHub `ubuntu-latest` x86_64, AMD EPYC 7763 CPU |
| Runtime/model | whisper.cpp `978113305b2e...`; `ggml-tiny.en.bin` SHA-256 `921e4cf8...` |

This small English read-speech sample is useful for reproducibility, not a
claim about conversational speech, noise, accents, other languages, laptops,
or hardware acceleration. The local backend remains experimental and
source-only until its package and real-device first-success gates pass.
