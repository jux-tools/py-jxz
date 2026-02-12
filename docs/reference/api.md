<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# API Reference

Complete Python API reference for py-jxz v0.1.5.

## ContainerBuilder

Build `.jxz` containers from JUnit XML reports and attachments.

```python
from jxz import ContainerBuilder
```

### Constructor

```python
ContainerBuilder()
```

Creates a new builder with no report, attachments, or metadata.

### Methods

#### `set_report(data: bytes) -> None`

Set or replace the JUnit XML report.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `bytes` | JUnit XML content |

#### `add_attachment(name: str, data: bytes, *, attachment_for: str | None = None) -> None`

Add an attachment to the container.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Relative path under `attachments/` (e.g. `screenshot.png`) |
| `data` | `bytes` | Attachment content |
| `attachment_for` | `str \| None` | Optional test identifier this attachment belongs to |

**Raises**: `PathTraversalError` if `name` contains `..` or starts with `/`.

#### `add_meta(name: str, data: bytes) -> None`

Add a metadata file under `META-INF/`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Filename (e.g. `pytest-metadata.json`) |
| `data` | `bytes` | File content |

**Raises**: `PathTraversalError` if `name` contains `..` or starts with `/`.

#### `build(*, created_by: str, report_type: str, timestamp: datetime | None = None, private_key: PrivateKey | None = None, certificate: Certificate | None = None) -> bytes`

Build the `.jxz` container and return the complete ZIP as bytes.

| Parameter | Type | Description |
|-----------|------|-------------|
| `created_by` | `str` | Tool identifier (e.g. `pytest-jux/0.1.0`) |
| `report_type` | `str` | Report dialect (e.g. `pytest-junit`) |
| `timestamp` | `datetime \| None` | Creation timestamp; defaults to `datetime.now(UTC)` |
| `private_key` | `PrivateKey \| None` | RSA or ECDSA key for signing |
| `certificate` | `Certificate \| None` | X.509 certificate to embed in signature |

**Returns**: Complete `.jxz` container as `bytes`.

**Raises**:

- `ContainerStructureError` if no report has been set.
- `SignatureError` if signing fails.

---

## ContainerReader

Read and verify `.jxz` containers.

```python
from jxz import ContainerReader
```

### Constructor

```python
ContainerReader(data: bytes)
```

Open a `.jxz` container from bytes.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `bytes` | Complete `.jxz` container bytes |

**Raises**:

- `ContainerStructureError` if not a valid ZIP or missing required entries (`META-INF/MANIFEST.MF`, `junit.xml`).
- `PathTraversalError` if any ZIP entry contains path traversal.

### Properties

#### `created_by: str`

Producer tool identifier from the manifest `Created-By` field.

#### `report_type: str`

Report dialect from the manifest `Report-Type` field.

#### `timestamp: datetime`

Container creation timestamp, parsed from the manifest `Timestamp` field (ISO 8601).

#### `is_signed: bool`

Whether the container has a `META-INF/SIGNATURE.XML` entry.

### Methods

#### `get_manifest() -> Manifest`

Return the parsed manifest.

#### `get_report() -> bytes`

Return the JUnit XML report bytes.

#### `get_attachments() -> dict[str, bytes]`

Return attachments as a dict of relative path to bytes. Keys are paths relative to `attachments/` (e.g. `screenshot.png`).

#### `get_meta() -> dict[str, bytes]`

Return META-INF extras, excluding `MANIFEST.MF` and `SIGNATURE.XML`. Keys are filenames only (e.g. `pytest-metadata.json`).

#### `get_signature_xml() -> bytes | None`

Return raw `SIGNATURE.XML` bytes, or `None` if the container is unsigned.

#### `list_entries() -> list[str]`

Return all entry paths in the container.

#### `validate() -> None`

Validate file digests and sizes against the manifest.

**Raises**:

- `DigestMismatchError` if any file's SHA-256 doesn't match.
- `ContainerStructureError` if a manifest entry is missing from the ZIP.

#### `verify(certificate: Certificate | None = None) -> None`

Verify container integrity: signature (if signed), then digests.

Verification order:
1. If signed, verify the XML signature against the manifest.
2. Validate manifest digests (same as `validate()`).

Unsigned containers pass signature verification — policy enforcement (rejecting unsigned containers) is the caller's responsibility.

| Parameter | Type | Description |
|-----------|------|-------------|
| `certificate` | `Certificate \| None` | X.509 certificate for signature verification |

**Raises**:

- `SignatureError` if the signature is invalid or content doesn't match.
- `DigestMismatchError` if any file's SHA-256 doesn't match.
- `ContainerStructureError` if a manifest entry is missing from the ZIP.

---

## Manifest

Parsed `.jxz` manifest with main section and per-file entries.

```python
from jxz import Manifest
```

### Dataclass Fields

```python
@dataclass
class Manifest:
    main: dict[str, str]           # Main section key-value pairs
    entries: list[dict[str, str]]  # Per-file entry sections
```

**Main section keys** (required): `Manifest-Version`, `Jux-Version`, `Created-By`, `Report-Type`, `Timestamp`.

**Entry keys** (required): `Name`, `SHA-256`, `Size`. Optional: `Attachment-For`.

---

## Manifest Module Functions

```python
from jxz.manifest import generate, parse, compute_digest
```

### `generate(manifest: Manifest) -> str`

Serialize a `Manifest` to JAR-style text.

Format: key-value pairs separated by `: ` (colon-space), sections separated by blank lines, trailing newline after last section.

### `parse(text: str) -> Manifest`

Parse JAR-style manifest text into a `Manifest`.

**Raises**: `ManifestError` if the text is empty, malformed, or missing required fields.

### `compute_digest(data: bytes) -> str`

Compute SHA-256 hex digest of data.

---

## Signing Functions

```python
from jxz import sign_container, sign_manifest, verify_signature
```

### `sign_manifest(manifest_text: str, private_key: PrivateKey, certificate: Certificate | None = None) -> bytes`

Sign manifest text using enveloping XMLDSIG. The manifest text is embedded inside a `<ds:Object>` element within the signature.

| Parameter | Type | Description |
|-----------|------|-------------|
| `manifest_text` | `str` | The `MANIFEST.MF` content to sign |
| `private_key` | `PrivateKey` | RSA or ECDSA private key |
| `certificate` | `Certificate \| None` | X.509 certificate to embed in signature |

**Returns**: `SIGNATURE.XML` content as UTF-8 bytes.

**Raises**: `SignatureError` if signing fails or the key type is unsupported.

### `sign_container(data: bytes, private_key: PrivateKey, certificate: Certificate | None = None, *, force: bool = False) -> bytes`

Sign (or re-sign) an existing `.jxz` container. Reads the container, validates digests, signs the manifest, and returns a new container with `META-INF/SIGNATURE.XML` added.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `bytes` | Complete `.jxz` container bytes |
| `private_key` | `PrivateKey` | RSA or ECDSA private key |
| `certificate` | `Certificate \| None` | X.509 certificate to embed in signature |
| `force` | `bool` | If `True`, allow re-signing an already-signed container |

**Returns**: New `.jxz` container bytes with signature.

**Raises**:

- `SignatureError` if the container is already signed and `force` is `False`.
- `ContainerStructureError` if the container is invalid.
- `DigestMismatchError` if digest validation fails.

### `verify_signature(signature_xml: bytes, manifest_text: str, certificate: Certificate | None = None) -> None`

Verify a `SIGNATURE.XML` against manifest text. Verifies the XML digital signature, then compares the signed content against the expected manifest text.

| Parameter | Type | Description |
|-----------|------|-------------|
| `signature_xml` | `bytes` | The `SIGNATURE.XML` content |
| `manifest_text` | `str` | The expected `MANIFEST.MF` content |
| `certificate` | `Certificate \| None` | X.509 certificate for verification; if `None`, uses the key embedded in the signature |

**Raises**: `SignatureError` if signature verification fails or content doesn't match.

---

## Type Aliases

### `PrivateKey`

```python
from jxz.signing import PrivateKey

PrivateKey = Union[rsa.RSAPrivateKey, ec.EllipticCurvePrivateKey]
```

Union of RSA and ECDSA private key types from the `cryptography` library.

---

## Error Hierarchy

All exceptions inherit from `JxzError`.

```
JxzError
├── ManifestError
├── DigestMismatchError
├── SignatureError
├── ContainerStructureError
└── PathTraversalError
```

```python
from jxz import (
    JxzError,
    ManifestError,
    DigestMismatchError,
    SignatureError,
    ContainerStructureError,
    PathTraversalError,
)
```

### `JxzError`

Base exception for all `.jxz` container errors.

### `ManifestError`

Error in manifest parsing or generation.

### `DigestMismatchError`

SHA-256 digest does not match manifest entry.

| Attribute | Type | Description |
|-----------|------|-------------|
| `entry_name` | `str` | Name of the file with mismatched digest |
| `expected` | `str` | Expected SHA-256 hex digest |
| `actual` | `str` | Actual SHA-256 hex digest |

### `SignatureError`

Error in signature creation or verification.

### `ContainerStructureError`

Container is missing required entries or has invalid structure.

### `PathTraversalError`

ZIP entry contains path traversal (ZIP slip protection).

| Attribute | Type | Description |
|-----------|------|-------------|
| `entry_name` | `str` | The offending entry path |
