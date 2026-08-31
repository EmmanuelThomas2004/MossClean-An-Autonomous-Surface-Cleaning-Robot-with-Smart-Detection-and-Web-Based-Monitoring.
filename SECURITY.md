# Security Policy

## Overview

MossClean combines robotics, edge AI, computer vision, embedded hardware, and web-based monitoring. Security is therefore considered across both the software and physical system.

## Supported Versions

Security fixes are primarily applied to the latest version of MossClean available in the repository.

| Version | Supported |
|---|---|
| Latest | ✅ |
| Older versions | ⚠️ Limited |

## Reporting a Vulnerability

If you discover a security vulnerability in MossClean, please report it privately rather than publicly exposing the issue.

Security-related reports may include:

- Authentication vulnerabilities
- Credential exposure
- Unauthorized dashboard access
- Remote command vulnerabilities
- Unsafe API behavior
- Sensitive information disclosure
- Web application security issues
- Hardware-control security concerns

Please provide enough information to reproduce the issue, including relevant logs, affected components, and reproduction steps where possible.

## Secrets and Credentials

Never commit the following to the repository:

- Passwords
- API keys
- SMTP credentials
- Access tokens
- Private keys
- `.env` files containing secrets
- Personal authentication information

Use environment variables or local configuration files for sensitive values.

## Hardware Security

MossClean controls physical hardware including motors, relays, pumps, and sensors.

Any modification involving hardware actuation should be tested carefully and validated in a controlled environment before deployment.

## Responsible Disclosure

Please allow reasonable time for a vulnerability to be investigated and addressed before publicly disclosing sensitive security details.

Thank you for helping keep MossClean secure.
