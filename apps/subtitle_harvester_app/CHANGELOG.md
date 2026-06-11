# Changelog

All notable changes to `subtitle-harvester-app` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows semantic versioning while it remains app-local.

## [0.1.0] - 2026-06-11

### Added

- Initial TMDb subtitle candidate harvester CLI.
- JSON output writer for normalized media candidates.
- App-local settings, logging bootstrap, Docker configuration, Make targets, tests, and `.env.example` generation.
- Project documentation and generated-output ignore rules.

### Fixed

- Replaced the template console script name with `subtitle-harvester-app`.
- Made CLI tests run offline without requiring a live TMDb request.
