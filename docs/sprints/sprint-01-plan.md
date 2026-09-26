# Sprint 1: Core Container Operations

## Context

py-jxz is at v0.1.0 with only scaffolding and the error hierarchy implemented. The three core modules (`manifest.py`, `builder.py`, `reader.py`) are stubs. Sprint 1 implements unsigned container building, reading, and digest validation — signing is deferred to Sprint 2.

Source of truth: `../jux-container-format/specs/v1/jxz-format.md` and `manifest-schema.json`.

## Implementation Order

### 1. `src/jxz/manifest.py` — Manifest generation and parsing

**Data model:**
- `ManifestMainSection` — TypedDict for the 5 required main fields (`Manifest-Version`, `Jux-Version`, `Created-By`, `Report-Type`, `Timestamp`)
- `ManifestEntry` — TypedDict for per-file entries (`Name`, `SHA-256`, `Size`, optional `Attachment-For`)
- `Manifest` — dataclass holding `main: dict[str, str]` and `entries: list[ManifestEntry]`

**Functions:**
- `generate(manifest: Manifest) -> str` — serialize to JAR-style text (main section, blank line, per-entry sections separated by blank lines)
- `parse(text: str) -> Manifest` — parse JAR-style text back into a `Manifest`. Raises `ManifestError` on malformed input.
- `compute_digest(data: bytes) -> str` — SHA-256 hex digest helper (used by both builder and reader)

**Format rules** (from spec):
- Key-value pairs separated by `: ` (colon-space)
- Sections separated by blank lines
- Main section first, then per-entry sections
- Trailing newline after last section

### 2. `tests/unit/test_manifest.py` — Manifest tests

- Round-trip: generate then parse recovers the same data
- Parse the complete example from the spec
- generate produces expected text format
- Handles unknown/extra fields (additionalProperties: true in schema)
- `ManifestError` on malformed input (missing required fields, bad format)
- `compute_digest` produces correct SHA-256 hex strings
- Property-based tests (hypothesis) for round-trip stability

### 3. `src/jxz/builder.py` — ContainerBuilder

**Class: `ContainerBuilder`**
```python
class ContainerBuilder:
    def set_report(self, data: bytes) -> None: ...
    def add_attachment(
        self, name: str, data: bytes, *, attachment_for: str | None = None
    ) -> None: ...
    def add_meta(
        self, name: str, data: bytes
    ) -> None: ...  # e.g., pytest-metadata.json
    def build(
        self, *, created_by: str, report_type: str, timestamp: datetime | None = None
    ) -> bytes: ...
```

**`build()` logic** (per spec signing process, minus step 4):
1. Validate: report must be set, no path traversal in attachment names
2. Compute SHA-256 digests for all files (junit.xml, attachments/*, META-INF extras)
3. Build `Manifest` with main section + per-entry sections
4. Generate `META-INF/MANIFEST.MF` text via `manifest.generate()`
5. Assemble ZIP in-memory (`io.BytesIO` + `zipfile.ZipFile`) with DEFLATE compression
6. Return ZIP bytes

**Constraints:**
- Attachment names must not contain `..` or start with `/` (PathTraversalError)
- `add_meta` names are placed under `META-INF/` (e.g., `pytest-metadata.json` → `META-INF/pytest-metadata.json`)
- `build()` is idempotent — can be called multiple times
- `set_report` can be called again to replace the report

### 4. `tests/unit/test_builder.py` — Builder tests

- Build minimal container (report only), verify it's a valid ZIP with expected entries
- Build with attachments, verify entries and content
- Build with `add_meta`, verify META-INF entries
- `attachment_for` field appears in manifest
- Raises `ContainerStructureError` if report not set
- Raises `PathTraversalError` for malicious attachment names (`../etc/passwd`, absolute paths)
- Timestamp defaults to now, or uses provided value
- Idempotent: calling `build()` twice produces equivalent archives

### 5. `src/jxz/reader.py` — ContainerReader

**Class: `ContainerReader`**
```python
class ContainerReader:
    def __init__(
        self, data: bytes
    ) -> None: ...  # raises ContainerStructureError if not valid ZIP or missing required entries
    def get_manifest(self) -> Manifest: ...
    def get_report(self) -> bytes: ...
    def get_attachments(
        self,
    ) -> dict[str, bytes]: ...  # keys are paths relative to attachments/
    def list_entries(self) -> list[str]: ...
    def validate(self) -> None: ...  # digest validation; raises DigestMismatchError
```

**`__init__` logic:**
1. Open ZIP from bytes (`io.BytesIO`)
2. Verify required entries exist: `META-INF/MANIFEST.MF`, `junit.xml`
3. Check for path traversal in all ZIP entry names
4. Parse manifest via `manifest.parse()`

**`validate()` logic** (per spec verification process, steps 3-4 only in Sprint 1):
1. For each entry in manifest, read file from ZIP, compute SHA-256
2. Compare to manifest digest — raise `DigestMismatchError` on mismatch
3. Verify Size field matches actual size

### 6. `tests/unit/test_reader.py` — Reader tests

- Read a builder-produced container, verify report and attachments
- `validate()` passes on an intact container
- `validate()` raises `DigestMismatchError` on tampered content
- `ContainerStructureError` on missing `junit.xml` or `MANIFEST.MF`
- `ContainerStructureError` on non-ZIP input
- `PathTraversalError` on ZIP with malicious entry names
- `list_entries()` returns all entry paths
- `get_attachments()` returns correct mapping

### 7. `tests/integration/test_round_trip.py` — Integration tests

- Build → Read → validate round-trip with report only
- Build → Read → validate round-trip with report + attachments + meta
- Verify extracted content matches original input byte-for-byte

### 8. `tests/conftest.py` — Shared fixtures

- `sample_junit_xml` — minimal valid JUnit XML bytes
- `sample_attachment` — small PNG-like bytes
- `sample_jxz_bytes` — pre-built unsigned container for reader tests

### 9. `src/jxz/__init__.py` — Public API exports

Export: `ContainerBuilder`, `ContainerReader`, `Manifest`, `__version__`, and error classes.

### 10. Housekeeping

- Update `CHANGELOG.md` with Sprint 1 additions
- Bump version to `0.1.1`

## Files Modified

| File | Action |
|------|--------|
| `src/jxz/manifest.py` | Implement |
| `src/jxz/builder.py` | Implement |
| `src/jxz/reader.py` | Implement |
| `src/jxz/__init__.py` | Add exports |
| `tests/conftest.py` | Add shared fixtures |
| `tests/unit/test_manifest.py` | Create |
| `tests/unit/test_builder.py` | Create |
| `tests/unit/test_reader.py` | Create |
| `tests/integration/test_round_trip.py` | Create |
| `CHANGELOG.md` | Update |
| `pyproject.toml` | Bump version |

## Verification

```bash
uv run pytest --cov=jxz --cov-report=term-missing   # all tests pass, >85% coverage
uv run ruff check .                                   # no lint errors
uv run ruff format --check .                          # formatting ok
uv run mypy src/jxz                                   # no type errors
```
