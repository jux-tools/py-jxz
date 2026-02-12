# py-jxz

Python library for building, reading, and verifying `.jxz` signed containers as specified by [jux-container-format](../jux-container-format/specs/v1/jxz-format.md).

## Project Context

- **Category**: Development
- **Type**: Python library
- **Stack**: Python 3.11+, signxml, cryptography
- **License**: Apache-2.0
- **Ecosystem**: Part of jux-tools workspace (see `../CLAUDE.md`)

## Purpose

py-jxz implements the `.jxz` container format in Python, providing:

| Module | Purpose | Used By |
|--------|---------|---------|
| `jxz.builder` | Build `.jxz` containers from JUnit XML + attachments | py-juxlib, pytest-jux, behave-jux |
| `jxz.manifest` | Generate and parse JAR-style `MANIFEST.MF` | builder, reader |
| `jxz.reader` | Extract, validate, and verify `.jxz` containers | py-juxlib, spooky |
| `jxz.signing` | XMLDSIG signing and verification (enveloping mode) | builder, reader |
| `jxz.cli` | CLI subcommands: inspect, verify, extract | end users, CI pipelines |

### Why a Separate Package

The `.jxz` format is consumed by both client libraries (py-juxlib) and servers (spooky). A standalone package avoids forcing servers to depend on py-juxlib (a client library with requests, metadata detection, etc.).

```
py-jxz                          <-- format implementation
├── used by py-juxlib            <-- client library
│   ├── used by pytest-jux
│   └── used by behave-jux
└── used by spooky               <-- FastAPI server
```

## Current Development Status

- **Completed Sprints**: Sprint 1 (core containers), Sprint 2 (XML signatures), Sprint 3 (API polish & CLI)
- **Latest Release**: v0.1.3
- **Next Milestone**: TBD (Sprint 4)

## Foundational ADRs

Read these at the start of each AI session for complete context:

| ADR | Purpose | Summary |
|-----|---------|---------|
| [ADR-0001](docs/adr/0001-record-architecture-decisions.md) | HOW TO DECIDE | Decision methodology |
| [ADR-0002](docs/adr/0002-adopt-development-best-practices.md) | HOW TO DEVELOP | Development practices |
| [ADR-0003](docs/adr/0003-use-python-technology-stack.md) | WHAT TECH | Technology stack |

## Development Practices

This project follows [AI-Assisted Project Orchestration patterns](https://github.com/jrjsmrtn/ai-assisted-project-orchestration):

- **Testing**: TDD with pytest, >85% coverage required
- **Versioning**: Semantic versioning (0.x.x during development)
- **Git Workflow**: Gitflow (main, develop, feature/*, release/*, hotfix/*)
- **Documentation**: Diataxis framework
- **Architecture**: C4 DSL models in `docs/architecture/`

## Quick Commands

```bash
# Setup development environment
uv venv && uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=jxz --cov-report=term-missing

# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type check
uv run mypy src/jxz
```

## Package Structure

```
src/jxz/
├── __init__.py          # Public API exports
├── __main__.py          # CLI entry point (python -m jxz)
├── py.typed             # PEP 561 marker
├── builder.py           # ContainerBuilder: assemble .jxz from parts
├── manifest.py          # Manifest generation and parsing (JAR format)
├── reader.py            # ContainerReader: extract and verify .jxz
├── signing.py           # XMLDSIG signing/verification (enveloping mode)
├── errors.py            # JxzError hierarchy
└── cli/
    ├── __init__.py      # Shared CLI utilities
    ├── inspect.py       # inspect subcommand
    ├── verify.py        # verify subcommand
    └── extract.py       # extract subcommand
```

## Dependencies

### Runtime Dependencies

```toml
[project.dependencies]
signxml = ">=4.0"            # XMLDSig signing/verification (detached)
cryptography = ">=42.0"      # RSA/ECDSA key handling
```

Standard library only for core operations: `zipfile`, `hashlib`, `tempfile`, `pathlib`.

### Optional Dependencies

```toml
[project.optional-dependencies]
cli = ["rich>=13.0"]     # Enhanced CLI output (optional)
dev = [...]              # Testing and linting tools
```

## AI Collaboration Notes

### Project-Specific Guidance

- **Source of truth**: [jux-container-format spec](../jux-container-format/specs/v1/jxz-format.md)
- **Sibling library**: py-juxlib will depend on py-jxz for container operations
- **Server consumer**: spooky (FastAPI) uses py-jxz for verification
- **No framework dependencies**: Library must not import pytest, requests, or pydantic
- **Minimal dependencies**: Only signxml + cryptography beyond stdlib

### Critical Constraints

1. **Python 3.11+ only** — Uses modern features (tomllib, type hints)
2. **No client-library imports** — Pure format library, no requests/pydantic
3. **In-memory by default** — Containers built and read as `bytes`
4. **Atomic operations** — Container building produces complete `.jxz` or raises
5. **Credential safety** — Never log or display private keys

## Related Projects

| Project | Relationship |
|---------|--------------|
| `jux-container-format` | **Source of truth** for `.jxz` format specification |
| `py-juxlib` | Client library that depends on py-jxz |
| `pytest-jux` | Test plugin that produces `.jxz` via py-juxlib |
| `behave-jux` | Test plugin that produces `.jxz` via py-juxlib |
| `spooky` | FastAPI server that consumes `.jxz` via py-jxz |
| `jux` | Elixir server that consumes `.jxz` (independent implementation) |

## Git Configuration

See `CLAUDE.local.md` for remote URLs (homelab details excluded from version control).

```bash
# Branch strategy: Gitflow
# - main: Production releases only
# - develop: Active development
# - feature/*: Individual features
# - release/*: Release preparation
# - hotfix/*: Critical fixes
```
