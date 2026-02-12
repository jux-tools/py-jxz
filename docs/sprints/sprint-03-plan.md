# Sprint 3: API Polish & CLI Tooling

## Goal

Add reader convenience accessors and a `python -m jxz` CLI with inspect, verify, and extract subcommands.

## Deliverables

### Part 1: Reader API Polish

- `ContainerReader.get_meta()` — META-INF extras as dict (excludes MANIFEST.MF/SIGNATURE.XML)
- `ContainerReader.get_signature_xml()` — raw SIGNATURE.XML bytes or None
- `ContainerReader.created_by` property — producer tool identifier
- `ContainerReader.report_type` property — report dialect
- `ContainerReader.timestamp` property — parsed ISO 8601 datetime

### Part 2: CLI Tooling

- `python -m jxz inspect <file.jxz> [--json]` — container metadata and file listing
- `python -m jxz verify <file.jxz> [--cert <cert.pem>] [--quiet] [--json]` — integrity verification
- `python -m jxz extract <file.jxz> [--output <dir>] [--report-only] [--attachments-only]` — content extraction
- `jxz` console script entry point
- Optional `cli` extra with rich for enhanced output

## Files Changed

| File | Action |
|------|--------|
| `src/jxz/reader.py` | Modified — added convenience methods and properties |
| `src/jxz/cli/__init__.py` | Created — shared CLI utilities |
| `src/jxz/cli/inspect.py` | Created — inspect subcommand |
| `src/jxz/cli/verify.py` | Created — verify subcommand |
| `src/jxz/cli/extract.py` | Created — extract subcommand |
| `src/jxz/__main__.py` | Created — CLI dispatcher |
| `src/jxz/__init__.py` | Modified — version bump to 0.1.3 |
| `pyproject.toml` | Modified — version, scripts, cli extra |
| `tests/conftest.py` | Modified — added meta fixtures |
| `tests/unit/test_reader.py` | Modified — added accessor tests |
| `tests/unit/test_cli_inspect.py` | Created |
| `tests/unit/test_cli_verify.py` | Created |
| `tests/unit/test_cli_extract.py` | Created |
| `CHANGELOG.md` | Updated |

## Verification

- 108 tests passing
- 89% code coverage (>85% threshold)
- ruff lint: clean
- ruff format: clean
- mypy strict: clean
