<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# ADR-0003: Use Python Technology Stack

Date: 2026-02-12

## Status

Accepted

## Context

py-jxz needs to build, read, and verify `.jxz` signed containers. The technology choices must balance:

- Minimal dependency footprint (this is a low-level library)
- Compatibility with both py-juxlib (client) and spooky (server) consumers
- Reliable cryptographic operations (XMLDSIG signing/verification)
- Standard ZIP handling

## Decision

### Runtime Dependencies

| Dependency | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| `signxml` | >=4.0 | XMLDSIG detached signatures | Same library used by py-juxlib for enveloped signing; well-maintained, W3C compliant |
| `cryptography` | >=42.0 | RSA/ECDSA key handling | Transitive via signxml; also used directly for key loading |

### Standard Library (No Additional Dependencies)

| Module | Purpose |
|--------|---------|
| `zipfile` | ZIP creation and extraction (DEFLATE) |
| `hashlib` | SHA-256 digest computation |
| `tempfile` | Temporary directories for extraction |
| `pathlib` | Path handling and validation |
| `io` | In-memory byte stream operations |

### Deliberately Excluded

| Library | Reason for Exclusion |
|---------|---------------------|
| `requests` | HTTP is py-juxlib's concern, not format handling |
| `pydantic` | Data validation is consumer's concern |
| `lxml` | Not needed for manifest parsing (plain text, not XML) |
| `rich` | Error formatting is consumer's concern |

### Build System

- **Build backend**: `hatchling` (modern, fast, PEP 517 compliant)
- **Package manager**: `uv` (fast dependency resolution)
- **Python version**: >=3.11 (tomllib, modern type hints)

### Development Tools

| Tool | Purpose |
|------|---------|
| `pytest` | Testing framework |
| `pytest-cov` | Coverage measurement |
| `hypothesis` | Property-based testing |
| `ruff` | Linting and formatting (replaces black, isort, flake8) |
| `mypy` | Static type checking (strict mode) |
| `pre-commit` | Git hook management |

## Consequences

### Positive

- **Two runtime dependencies** only — minimal install footprint
- **signxml** already proven in the Jux ecosystem (py-juxlib, pytest-jux)
- **Standard library** handles core operations (ZIP, hashing, temp files)
- **No web/API dependencies** — clean separation from client/server concerns
- **Type-safe** — mypy strict mode catches errors at development time

### Negative

- `signxml` pulls in `lxml` and `cryptography` as transitive dependencies
- Python 3.11+ requirement excludes older environments
- `hatchling` is less common than `setuptools` (but cleaner configuration)

## References

- [signxml documentation](https://github.com/XML-Security/signxml)
- [PEP 517 - Build system interface](https://peps.python.org/pep-0517/)
- [hatchling documentation](https://hatch.pypa.io/)
