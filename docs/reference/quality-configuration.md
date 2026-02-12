<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Quality Configuration Reference

Single source of truth for all quality tool settings in py-jxz.

## Formatting Standards

| Setting | Value | Configured In |
|---------|-------|---------------|
| Line length | 88 | pyproject.toml `[tool.ruff]` |
| Quote style | Double | pyproject.toml `[tool.ruff.format]` |
| Indent style | 4 spaces (Python) | .editorconfig, pyproject.toml |
| Indent style | 2 spaces (YAML/JSON/TOML/MD) | .editorconfig |
| Line endings | LF | .editorconfig |
| Trailing whitespace | Trim (except .md) | .editorconfig, pre-commit |
| Final newline | Required | .editorconfig, pre-commit |

## Quality Checks by Stage

### Pre-commit (<30 seconds)

| Check | Tool | Auto-fix |
|-------|------|----------|
| Trailing whitespace | pre-commit-hooks | Yes |
| File hygiene | pre-commit-hooks | Yes |
| Secret detection | gitleaks | No (block) |
| Linting | ruff check | Yes |
| Formatting | ruff format | Yes |

### Pre-push (<3 minutes)

| Check | Tool | Auto-fix |
|-------|------|----------|
| Type checking | mypy (strict) | No |
| Fast tests | pytest (not slow) | No |

### CI/CD

| Check | Tool | Threshold |
|-------|------|-----------|
| Full test suite | pytest | >85% coverage |
| Type checking | mypy | Zero errors |
| Linting | ruff | Zero warnings |

## Tool Versions

| Tool | Minimum Version | Purpose |
|------|-----------------|---------|
| Python | 3.11 | Runtime |
| ruff | 0.4 | Linting + formatting |
| mypy | 1.10 | Type checking |
| pytest | 8.0 | Testing |
| pytest-cov | 4.0 | Coverage |
| pre-commit | 3.0 | Hook management |
| gitleaks | 8.21.2 | Secret detection |

## Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | ruff, mypy, pytest, coverage settings |
| `.pre-commit-config.yaml` | Hook definitions and stages |
| `.editorconfig` | Editor formatting rules |
| `.gitleaksignore` | Secret detection exceptions |
