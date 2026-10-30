# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| latest  | ✅                 |

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Report vulnerabilities by emailing the maintainer directly via GitHub.
Expect acknowledgement within 48 hours and a resolution plan within 7 days.

## Scope

- Hardcoded credentials or API keys in source code
- SQL injection, command injection, or SSRF in anomaly detection pipelines
- Weak default secrets in `docker-compose.yml`
- Unsafe deserialization of model artefacts

## Out of Scope

- Theoretical vulnerabilities with no working proof-of-concept
- Issues in third-party libraries that already have a public CVE and no patch

## Credential Rotation

If a secret is leaked:
1. Rotate the credential immediately in your secrets manager
2. Audit ingestion logs for the affected time window
3. Report the incident via the contact above

## Security Best Practices

- Copy `.env.example` to `.env` and fill in real values — never commit `.env`
- Pin all dependency versions in `pyproject.toml`
- Run `pip-audit` or `safety check` before each release
