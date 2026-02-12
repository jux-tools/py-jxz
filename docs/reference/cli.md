<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# CLI Reference

Command-line interface for building, inspecting, verifying, and extracting `.jxz` containers.

## Installation

The CLI is available as a console script when py-jxz is installed:

```bash
pip install py-jxz        # minimal (CLI works without extras)
pip install py-jxz[cli]   # with rich for enhanced output
```

The CLI can also be invoked as a Python module:

```bash
python -m jxz
```

## Global Options

```
jxz [--version] [--help] <command>
```

| Flag | Description |
|------|-------------|
| `--version` | Show version and exit |
| `--help`, `-h` | Show help and exit |

---

## `jxz build`

Assemble a `.jxz` container from a JUnit XML report, optional attachments, and optional signing materials.

```
jxz build REPORT --created-by TEXT --report-type TYPE
          [--attachment PATH[:TEST_ID]] ...
          [--meta FILE] ...
          [--key PEM] [--cert PEM]
          [-o PATH] [--timestamp ISO8601]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `REPORT` | Path to JUnit XML report file |

### Flags

| Flag | Description |
|------|-------------|
| `--created-by TEXT` | Tool identifier (e.g. `pytest-jux/0.1.0`) — **required** |
| `--report-type TYPE` | Report dialect (e.g. `pytest-junit`) — **required** |
| `--attachment PATH[:TEST_ID]` | Attachment file, repeatable. Optionally suffix `:TEST_ID` to set `Attachment-For` |
| `--meta FILE` | File to add under `META-INF/`, repeatable |
| `--key PEM` | Private key PEM file for signing (RSA or ECDSA, auto-detected) |
| `--cert PEM` | Certificate PEM file (requires `--key`) |
| `--output PATH`, `-o PATH` | Output path (default: `<report>.jxz`) |
| `--timestamp ISO8601` | ISO 8601 timestamp (default: now UTC) |

### Behavior

- Reads the report file and all referenced attachments/meta files.
- Builds the container in memory using `ContainerBuilder`.
- If `--key` is provided, signs the manifest. If `--cert` is also provided, embeds the certificate in the signature.
- Creates parent directories for the output path if needed.
- Prints the resolved output path to stdout on success.

### Output

Prints the output file path to stdout:

```
/path/to/report.jxz
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Container built successfully |
| 1 | Missing file, invalid arguments, or build failure |

---

## `jxz inspect`

Display container metadata and file inventory.

```
jxz inspect [--json] FILE
```

### Arguments

| Argument | Description |
|----------|-------------|
| `FILE` | Path to `.jxz` file |

### Flags

| Flag | Description |
|------|-------------|
| `--json` | Output as JSON instead of human-readable format |

### Human-Readable Output

```
Container: report.jxz
  Created-By:  pytest-jux/0.1.0
  Report-Type: pytest-junit
  Timestamp:   2026-01-15T10:30:00+00:00
  Signed:      Yes (RSA-SHA256)

Files (2):
  Name                                       Size   SHA-256
  junit.xml                                 4.5 KB   7d865e95...
  attachments/screenshot.png               44.2 KB   e3b0c442...
```

### JSON Output

```json
{
  "file": "report.jxz",
  "created_by": "pytest-jux/0.1.0",
  "report_type": "pytest-junit",
  "timestamp": "2026-01-15T10:30:00+00:00",
  "signed": true,
  "signature": "Yes (RSA-SHA256)",
  "files": [
    {
      "name": "junit.xml",
      "size": 4521,
      "sha256": "7d865e959b2466918c9863afca942d0fb89d7c9ac0c99bafc3749504ded97730"
    }
  ]
}
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | File not found or invalid container |

---

## `jxz verify`

Verify container integrity and optionally verify the signature against a certificate.

```
jxz verify [--cert PEM] [--quiet] [--json] FILE
```

### Arguments

| Argument | Description |
|----------|-------------|
| `FILE` | Path to `.jxz` file |

### Flags

| Flag | Description |
|------|-------------|
| `--cert PEM` | PEM certificate file for signature verification |
| `--quiet` | Suppress output on success (exit code only) |
| `--json` | Output as JSON |

### Behavior

1. Opens the container and parses the manifest.
2. If signed and `--cert` is provided, verifies the XML signature against the certificate.
3. If signed and no `--cert`, verifies the signature using the key embedded in the signature.
4. Validates all file digests against the manifest.

Unsigned containers pass verification (no signature to check). Use application-level policy to reject unsigned containers if needed.

### Output

**Success (default)**:
```
OK
```

**Success (JSON)**:
```json
{"status": "ok", "message": "Verification passed"}
```

**Failure (default)**: prints error to stderr.

**Failure (JSON)**:
```json
{"status": "error", "message": "Digest mismatch for junit.xml: expected abc..., got def..."}
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Verification passed |
| 1 | Verification failed, file not found, or invalid container |

---

## `jxz extract`

Extract container contents to disk. Validates digests before extracting.

```
jxz extract [--output DIR] [--report-only] [--attachments-only] FILE
```

### Arguments

| Argument | Description |
|----------|-------------|
| `FILE` | Path to `.jxz` file |

### Flags

| Flag | Description |
|------|-------------|
| `--output DIR`, `-o DIR` | Output directory (default: current directory) |
| `--report-only` | Extract only `junit.xml` |
| `--attachments-only` | Extract only `attachments/` |

### Behavior

- Without flags: extracts `junit.xml`, `attachments/*`, and META-INF extras.
- `--report-only`: extracts only `junit.xml`.
- `--attachments-only`: extracts only files under `attachments/`.
- Creates output directory and subdirectories as needed.
- Prints each extracted file path to stdout, one per line.

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | File not found, invalid container, or integrity check failed |
