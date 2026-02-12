# Sprint 1 Retrospective: Core Container Operations

**Sprint**: 1
**Date**: 2026-02-12
**Version**: 0.1.0 → 0.1.1

## Goals vs Outcomes

| Goal | Status | Notes |
|------|--------|-------|
| Manifest generation and parsing | Done | JAR-style format with round-trip fidelity |
| Container building (unsigned) | Done | ZIP/DEFLATE, in-memory, idempotent |
| Container reading and validation | Done | Digest + size verification |
| >85% test coverage | Done | 98.02% achieved |
| All quality gates pass | Done | pytest, ruff, mypy all green |

## Metrics

- **Tests**: 55 (18 manifest, 19 builder, 13 reader, 4 integration, 1 version)
- **Coverage**: 98.02% (branch coverage enabled)
- **Source lines**: ~475 added across 8 modified + 5 new files
- **Signing deferred**: As planned, XML signature support is Sprint 2 scope

## What Went Well

- Clean separation between manifest, builder, and reader modules
- Path traversal protection in both builder (input validation) and reader (ZIP entry scanning)
- Hypothesis property-based testing caught no issues but provides ongoing regression safety
- All runtime deps (signxml, cryptography) installed but unused — ready for Sprint 2

## What Could Improve

- `errors.py` formatting was reformatted by ruff — could pre-format skeleton files
- Initial tampered-report test assumed digest check runs before size check; fixed to use same-size tampered data

## Carry-Forward to Sprint 2

- XML signature support (signxml integration)
- `META-INF/SIGNATURE.XML` generation in builder
- Signature verification in reader
- Certificate/key handling
