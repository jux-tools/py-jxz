<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Sprint 6 Proposal: File-Backed I/O for Large Containers

## Motivation

The current API is entirely in-memory: `bytes` in, `bytes` out. This works well for typical containers (JUnit XML + a few screenshots, under 10 MB) but becomes a problem for containers with large attachments (video recordings, trace files, 100+ MB). Memory usage is proportional to the total container size, with `sign_container()` holding two full copies simultaneously.

## Goal

Add file-backed alternatives to builder, reader, and signing so that memory usage is proportional to the largest single entry, not the total container size. The existing `bytes`-based API stays unchanged — file-backed is additive.

## Constraint

The `.jxz` manifest must contain SHA-256 digests of all files and is the first entry in the ZIP. This means:
- **Builder**: two-pass (digest, then write) — cannot single-pass stream
- **Reader**: already lazy internally (`zipfile.ZipFile` reads entries on demand)
- **Signing**: copy entries one at a time from source ZIP to destination ZIP

## Deliverables

### Part 1: Builder — Path-Based Inputs

New methods on `ContainerBuilder`:

```python
def set_report_path(self, path: Path) -> None: ...
def add_attachment_path(self, name: str, path: Path, *, attachment_for: str | None = None) -> None: ...
def add_meta_path(self, name: str, path: Path) -> None: ...
def build_to(self, output: Path, *, created_by: str, report_type: str, ...) -> None: ...
```

- `set_report_path` / `add_attachment_path` / `add_meta_path` store `Path` references, not bytes
- `build_to()` does two passes:
  1. Read each file once to compute SHA-256 digests (one file at a time in memory)
  2. Write ZIP to `output`, re-reading each file for content
- Existing `set_report(bytes)` / `add_attachment(bytes)` / `build() -> bytes` remain unchanged
- Mixed usage (some bytes, some paths) is supported

### Part 2: Reader — File-Backed Construction

New classmethod on `ContainerReader`:

```python
@classmethod
def from_file(cls, path: Path) -> ContainerReader: ...
```

- Opens `zipfile.ZipFile` from a file path instead of `io.BytesIO(data)`
- All existing methods (`get_report()`, `get_attachments()`, `validate()`, etc.) work unchanged — `zipfile.ZipFile` already reads entries on demand
- Constructor `ContainerReader(data: bytes)` remains unchanged

### Part 3: Signing — File-to-File

New function in `jxz.signing`:

```python
def sign_container_file(
    src: Path,
    dst: Path,
    private_key: PrivateKey,
    certificate: Certificate | None = None,
    *,
    force: bool = False,
) -> None: ...
```

- Opens source ZIP, reads manifest, validates digests (one entry at a time)
- Signs manifest
- Writes destination ZIP: copies entries one at a time from source, adds SIGNATURE.XML
- Memory: one entry + signature XML at peak

### Part 4: CLI Updates

- `jxz build`: use `build_to()` when all inputs are file paths (the normal case)
- `jxz sign`: use `sign_container_file()` instead of `sign_container()`
- `jxz verify` / `jxz inspect` / `jxz extract`: use `ContainerReader.from_file()`
- Behavior is identical; only memory profile changes

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/jxz/builder.py` | Modify — add path-based methods and `build_to()` |
| `src/jxz/reader.py` | Modify — add `from_file()` classmethod |
| `src/jxz/signing.py` | Modify — add `sign_container_file()` |
| `src/jxz/__init__.py` | Modify — export `sign_container_file`, version bump |
| `src/jxz/cli/build.py` | Modify — use `build_to()` |
| `src/jxz/cli/sign.py` | Modify — use `sign_container_file()` |
| `src/jxz/cli/inspect.py` | Modify — use `from_file()` |
| `src/jxz/cli/verify.py` | Modify — use `from_file()` |
| `src/jxz/cli/extract.py` | Modify — use `from_file()` |
| `tests/unit/test_builder.py` | Modify — add path-based and build_to tests |
| `tests/unit/test_reader.py` | Modify — add from_file tests |
| `tests/unit/test_signing.py` | Modify — add sign_container_file tests |
| `tests/unit/test_cli_*.py` | Verify existing tests still pass (no new CLI tests needed) |
| `docs/reference/api.md` | Modify — document new methods |
| `CHANGELOG.md` | Modify |

## Estimated Scope

- ~10 modified files
- ~30-40 new tests
- No new dependencies
- Backward compatible (all existing APIs unchanged)

## Priority

**Low**. Typical `.jxz` containers are well under 10 MB (JUnit XML + screenshots). This becomes relevant when packaging video recordings, large trace files, or many attachments. Consider implementing when a concrete large-container use case arises.

## Open Questions

- Should `build_to()` accept a file-like object in addition to `Path`? (Increases flexibility but complicates the two-pass approach.)
- Should `from_file()` return a context manager to ensure the ZIP file handle is closed? (Current `bytes`-based reader doesn't need cleanup.)
- Should path-based methods validate that the file exists at add-time or at build-time? (Build-time is more consistent with the current deferred validation pattern.)
