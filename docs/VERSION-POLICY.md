# Supported versions and deprecation policy

## Support window

| Version | Support |
| --- | --- |
| Latest stable release | Bug, privacy, packaging, and security fixes are evaluated here first |
| Previous stable minor | Best-effort security guidance until 90 days after the next stable minor |
| Older releases, `main`, experimental local mode | No support promise; upgrade or reproduce on the latest stable release |

The project is maintained on a best-effort basis and does not promise a fix or
response SLA. Reproducible public bugs target acknowledgement within seven days;
security reports stay private until a coordinated fix is ready.

## Deprecation

- User-visible config, CLI schema, provider, package, or retention changes are
  announced in the changelog and release privacy section before removal.
- When safety permits, a deprecated path remains for at least one stable minor
  release with a direct migration action.
- A privacy or security flaw may require immediate disablement. Release notes
  must explain the impact, safe alternative, and data/config cleanup.
- Unknown config/history schema versions fail closed rather than being silently
  rewritten by an older app.

## Auditability

Release notes separate new behavior, privacy changes, verification, known
limitations, compatibility evidence, and migrations. Provider/model/package
changes must name exact versions or commits. Every automated release includes a
checksum, test report, CycloneDX SBOM, and provenance attestation.
