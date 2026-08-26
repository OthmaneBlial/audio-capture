# Reproducible provider benchmark

This harness compares transcription providers on the same deterministic slice
of LibriSpeech `test-clean`. It reports word-error counts plus p50/p95 wall-clock
latency; it does not turn those measurements into a context-free “accuracy”
marketing score.

LibriSpeech is published by OpenSLR as SLR12 under CC BY 4.0. The preparation
script accepts only the official `test-clean.tar.gz` MD5
`32fa31d27d2e1cad72775fee3f4849a9`, extracts it outside the repository, and
selects sorted utterances across sorted speakers. See the [corpus page](https://openslr.org/12/)
and its [checksum file](https://openslr.org/resources/12/md5sum.txt).

## Prepare 25 fixed samples

```bash
curl -LO https://openslr.org/resources/12/test-clean.tar.gz
python benchmarks/prepare_librispeech.py \
  --archive test-clean.tar.gz \
  --output-dir /tmp/voice-transcriber-librispeech \
  --sample-count 25
```

The archive is roughly 346 MB. No corpus files belong in Git.

## Run Groq cloud

```bash
export GROQ_API_KEY='your-tester-owned-key'
python benchmarks/run_benchmark.py \
  --manifest /tmp/voice-transcriber-librispeech/manifest.json \
  --provider groq \
  --provider-model whisper-large-v3-turbo \
  --hardware-label 'network run; CPU not material' \
  --output benchmarks/results/groq-example.json
```

Each sample is sent to Groq. Use a key and account you control, review the
current provider terms, and do not publish the key or request logs.

## Run experimental local whisper.cpp

Install `ffmpeg`, build `whisper-cli`, and download a GGML model you have
verified. Then record the exact CLI revision and model checksum in
`--provider-model`:

```bash
VOICE_TRANSCRIBER_EXPERIMENTAL_LOCAL=1 \
python benchmarks/run_benchmark.py \
  --manifest /tmp/voice-transcriber-librispeech/manifest.json \
  --provider local_whisper_cpp \
  --local-binary /opt/whisper.cpp/build/bin/whisper-cli \
  --local-model /opt/models/ggml-base.en.bin \
  --provider-model 'whisper.cpp REV + model SHA-256' \
  --hardware-label 'CPU model; RAM; acceleration details' \
  --output benchmarks/results/local-example.json
```

The current local path is an explicit source-install experiment. It is disabled
inside the Flatpak, downloads nothing automatically, and is not a supported
release backend until a real result receipt and the P1 packaging/first-success
gate both pass.

## Publishing a result

Review the receipt before committing it. A useful result names the exact model,
hardware, corpus checksum, sample and speaker count, WER numerator/denominator,
p50/p95 latency, limitations, and any failed samples. Never hand-edit summary
numbers; rerun the harness.

