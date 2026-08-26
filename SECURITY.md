# Security policy

## Supported version

Security fixes are applied to the latest `main` branch and the latest public release when practical.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for a suspected vulnerability, exposed credential, or privacy flaw. Use GitHub's private vulnerability-reporting feature for this repository when available, or contact the maintainer through the email address listed on the repository profile with:

- a concise description and impact;
- reproducible steps or a minimal proof of concept;
- affected version or commit; and
- any mitigation already tested.

Do not include real API keys, recordings, or transcript contents. We will acknowledge a good-faith report, investigate it privately, and coordinate disclosure after a fix is available.

## Scope notes

The app sends completed speech segments to Groq when transcription is active. Treat API-key handling, configuration permissions, export behavior, and unintended audio transmission as security-sensitive surfaces.
