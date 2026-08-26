# Security policy

## Supported versions

Security fixes are evaluated for the latest stable release first. The previous
stable minor receives best-effort security guidance for 90 days after its
successor; older releases, development snapshots, and experimental local mode
have no support promise. See the complete
[version/deprecation policy](docs/VERSION-POLICY.md).

## Reporting a vulnerability

Please **do not** open a public GitHub issue for a suspected vulnerability, exposed credential, or privacy flaw. Use GitHub's private vulnerability-reporting feature for this repository when available, or contact the maintainer through the email address listed on the repository profile with:

- a concise description and impact;
- reproducible steps or a minimal proof of concept;
- affected version or commit; and
- any mitigation already tested.

Do not include real API keys, recordings, or transcript contents. We will acknowledge a good-faith report, investigate it privately, and coordinate disclosure after a fix is available.

## Scope notes

The app sends completed speech segments to Groq when transcription is active. Treat API-key handling, configuration permissions, export behavior, and unintended audio transmission as security-sensitive surfaces.
