<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# ADR-0002: Adopt Development Best Practices

Date: 2026-02-12

## Status

Accepted

## Context

py-jxz is a format implementation library consumed by both client libraries (py-juxlib) and servers (spooky). This requires:

- High reliability (format handling must be correct)
- Clear, typed API for consumers
- Minimal dependency footprint
- Maintainability for long-term evolution

We need to establish development practices that ensure professional-quality output suitable for both internal use and potential public release.

## Decision

We adopt the following development best practices for py-jxz:

### 1. Test-Driven Development (TDD)

**Approach**: Red-Green-Refactor cycle for all new functionality

**Tools**:
- `pytest` for unit and integration testing
- `pytest-cov` for coverage measurement (>85% required)
- `hypothesis` for property-based testing of edge cases

**Test Organization**:
```
tests/
├── unit/           # Fast, isolated tests
│   ├── test_builder.py
│   ├── test_manifest.py
│   ├── test_reader.py
│   └── test_errors.py
├── integration/    # Round-trip and real .jxz tests
│   └── ...
├── fixtures/       # Test certificates and sample data
└── conftest.py     # Shared fixtures
```

### 2. Semantic Versioning

**Format**: MAJOR.MINOR.PATCH following [SemVer 2.0.0](https://semver.org/)

**Development Phase**: 0.x.x versioning during initial development
- 0.1.x: Core feature implementation
- Breaking changes allowed before 1.0.0
- Clear CHANGELOG entries for all changes

### 3. Git Workflow (Gitflow-Based)

**Branches**:
- `main`: Production releases only (protected)
- `develop`: Integration branch for ongoing development
- `feature/*`: Individual feature development
- `release/*`: Release preparation and stabilization
- `hotfix/*`: Critical fixes for production

**Commit Convention**: [Conventional Commits v1.0.0](https://www.conventionalcommits.org/)

### 4. Keep a Changelog

**Format**: [Keep a Changelog 1.1.0](https://keepachangelog.com/)

**Categories**: Added, Changed, Deprecated, Removed, Fixed, Security

### 5. Architecture as Code (C4 DSL)

**Tool**: Structurizr DSL
**Location**: `docs/architecture/`

### 6. Documentation Framework (Diataxis)

**Structure**:
```
docs/
├── tutorials/      # Learning-oriented
├── howto/          # Problem-oriented
├── reference/      # Information-oriented
└── explanation/    # Understanding-oriented
```

### 7. Sprint-Based Development

**Cycle**: 2-week sprints with planning, execution, review, and retrospective

### 8. Code Quality Automation

**Pre-commit Hooks** (two-stage):
- Stage 1 (pre-commit, <30s): ruff, gitleaks, file hygiene
- Stage 2 (pre-push, <3min): mypy, pytest

### 9. Type Hints

**Standard**: Full type hints for all public APIs
- `mypy` in strict mode
- `py.typed` marker for PEP 561 compliance
- `from __future__ import annotations` for forward references

## Consequences

**Positive**:
- High code quality maintained through automation
- Type safety reduces runtime errors for consumers
- Clear documentation for library users
- AI assistants have clear context from ADRs and documentation

**Negative**:
- Initial setup overhead for tooling
- Pre-commit hooks add time to commit cycle

**Trade-offs Accepted**:
- Strictness over speed: Quality automation adds overhead but prevents bugs
- Minimal docs initially: Focus on reference docs, expand tutorials later

## References

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/)
- [Keep a Changelog 1.1.0](https://keepachangelog.com/)
- [Diataxis Documentation Framework](https://diataxis.fr/)
- [PEP 561 - Distributing Type Information](https://peps.python.org/pep-0561/)
