# Security Policy

## Supported Versions

Only the latest released version is supported with security fixes.

## Scope

Screen Preview Tool runs entirely locally:

- No network calls, telemetry, or accounts — nothing leaves your machine.
- Screen captures (`mss`) exist only in memory for the live preview; nothing is written to disk.
- The window-moving feature (`pygetwindow` / `pywin32`) only repositions windows. It does not read window content or inject anything into other processes.

## Reporting a Vulnerability

Please **do not** open a public issue for security vulnerabilities.

Instead, use GitHub's private reporting:

1. Go to the **Security** tab of this repository.
2. Click **Report a vulnerability**.

Please include:
- A description of the issue and its potential impact
- Steps to reproduce
- Affected version(s)

## Dependencies

This project depends on `mss`, `pillow`, `pygetwindow`, and `pywin32`. These are tracked for known CVEs and updated periodically — Pillow in particular has a history of image-parsing CVEs, so it's checked most closely.

## Installer & Binary Integrity

Released installers (built with PyInstaller + Inno Setup) are **not code-signed**. Windows SmartScreen may warn on first run — this is expected for an unsigned binary, not necessarily a sign of tampering.
