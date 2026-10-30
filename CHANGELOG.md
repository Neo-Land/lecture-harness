# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]
### Fixed
- Verifier compared numbers as substrings, so "4 seconds" passed on a slide saying "0.42 seconds".
  Numbers now compare by value, sign, and unit; terms match whole words.
- Verifier now handles superscripts, unicode ligatures and dashes, simple LaTeX, and `5 ms` vs `5ms`.
- Facts inside visuals are now verified, and citations of blank slides fail.

### Added
- CI status badge, `/health` in the README endpoint table, ADR 0002 (FastAPI + SQLite + BM25).

### Changed
- Documented that visual contents are not verified yet; added the fix to Phase 1.

## [0.0.0] — 2026-10-30
### Added
- Backend scaffold: PDF/PPTX parsing, layered verifier, generate→verify→revise harness,
  BM25 retrieval, SQLite store, Canvas client, FastAPI endpoints.
- 25 offline tests (fake model, mocked Canvas API); 90% coverage.
- CI (ruff + pytest with 85% coverage gate, Python 3.11/3.13), Dependabot, PR template,
  Claude Code permission rules.
- Project docs: `CLAUDE.md`, project plan, architecture, setup/access guide, ADR 0001.
