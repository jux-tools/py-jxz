<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Sprint 4: `jxz build` CLI Subcommand

## Goal

Add a `jxz build` subcommand to assemble `.jxz` containers from the command line, making the tool self-contained for CI pipelines and manual use. Also address carry-forward items from Sprint 3 (`load_private_key` utility, CLI utility coverage).

## Deliverables

### Part 1: CLI Utility

- `load_private_key(path)` — mirrors `load_certificate()`, loads PEM key, `SystemExit(1)` on error

### Part 2: `jxz build` Subcommand

```
jxz build REPORT --created-by TEXT --report-type TYPE
          [--attachment PATH[:TEST_ID]] ...
          [--meta FILE] ...
          [--key PEM] [--cert PEM]
          [-o PATH] [--timestamp ISO8601]
```

- Required: report file, `--created-by`, `--report-type`
- Optional: attachments (with optional test_id), meta files, signing, timestamp, output path
- Prints resolved output path to stdout on success

## Files Changed

| File | Action |
|------|--------|
| `src/jxz/cli/__init__.py` | Modified — added `load_private_key()`, `PrivateKey` type import |
| `src/jxz/cli/build.py` | Created — build subcommand (~70 lines) |
| `src/jxz/__main__.py` | Modified — registered build, updated description |
| `src/jxz/__init__.py` | Modified — version bump to 0.1.4 |
| `pyproject.toml` | Modified — version bump to 0.1.4 |
| `tests/conftest.py` | Modified — added 7 file-based fixtures |
| `tests/unit/test_cli_utils.py` | Modified — added `TestLoadPrivateKey` (4 tests) |
| `tests/unit/test_cli_build.py` | Created — 31 tests across 8 classes |
| `docs/reference/cli.md` | Modified — added `jxz build` section |
| `docs/howto/use-cli.md` | Modified — added 5 build recipes |
| `CHANGELOG.md` | Modified — cut v0.1.4 release entry |
| `CLAUDE.md` | Modified — updated status to Sprint 4 / v0.1.4 |

## Verification

- 162 tests passing
- 97% code coverage (>85% threshold)
- ruff lint: clean
- ruff format: clean
- mypy strict: clean
