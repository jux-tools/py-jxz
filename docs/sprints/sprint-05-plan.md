<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Sprint 5: `jxz sign` CLI Subcommand

## Goal

Add a `jxz sign` subcommand to sign (or re-sign) an existing `.jxz` container. This decouples signing from building, enabling workflows where containers are built in CI and signed separately by a trusted authority.

## Context

Currently, signing is only possible during `jxz build`. There is no way to:
- Sign a container that was built without `--key`
- Re-sign a container with a different key
- Sign a container produced by a different tool

The reader already stores the raw manifest text (`_manifest_text`), which is the exact input needed for `sign_manifest()`. The implementation needs to repackage the ZIP with a `SIGNATURE.XML` entry added (or replaced).

## CLI Interface

```
jxz sign FILE --key PEM [--cert PEM] [-o PATH] [--force]
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `FILE` | Yes | Path to `.jxz` container |
| `--key` | Yes | Private key PEM file (RSA or ECDSA, auto-detected) |
| `--cert` | No | Certificate PEM file |
| `-o`/`--output` | No | Output path (default: overwrite input file in-place) |
| `--force` | No | Allow re-signing an already-signed container |

**Behavior**:
- Reads and validates the container (digests must pass).
- Refuses to sign an already-signed container unless `--force` is given.
- With `--force`, strips the existing `SIGNATURE.XML` before re-signing.
- Signs the manifest text with the provided key.
- Writes the new container (all original entries + `SIGNATURE.XML`).
- Default output is in-place (overwrite `FILE`), like `jarsigner`.
- Prints the output path to stdout on success (exit 0), error to stderr (exit 1).

## Library Addition

### `sign_container()` in `jxz/signing.py`

A library-level function so servers and libraries can also sign existing containers programmatically:

```python
def sign_container(
    data: bytes,
    private_key: PrivateKey,
    certificate: Certificate | None = None,
    *,
    force: bool = False,
) -> bytes:
```

- Reads the container via `ContainerReader`.
- Validates digests.
- Checks `is_signed`; raises `SignatureError` if signed and `force=False`.
- Signs the manifest text.
- Repackages the ZIP: copies all entries (excluding old `SIGNATURE.XML` if re-signing), adds new `SIGNATURE.XML`.
- Returns the new container bytes.

This keeps the CLI thin — it just loads files, calls `sign_container()`, and writes output.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/jxz/signing.py` | **Modify** — add `sign_container()` |
| `src/jxz/__init__.py` | **Modify** — export `sign_container`, version bump to 0.1.5 |
| `src/jxz/cli/sign.py` | **Create** — sign subcommand (~50 lines) |
| `src/jxz/__main__.py` | **Modify** — register sign subcommand |
| `tests/unit/test_signing.py` | **Modify** — add `TestSignContainer` (~8 tests) |
| `tests/unit/test_cli_sign.py` | **Create** — ~18 test cases |
| `docs/reference/cli.md` | **Modify** — add `jxz sign` section |
| `docs/reference/api.md` | **Modify** — add `sign_container()` |
| `docs/howto/use-cli.md` | **Modify** — add sign recipes |
| `CHANGELOG.md` | **Modify** — add entry under `[Unreleased]` |

## Implementation Order

### Step 1: `sign_container()` in `jxz/signing.py` + tests

Add the library function. It reads with `ContainerReader`, validates, signs, and repackages.

Add `TestSignContainer` to `tests/unit/test_signing.py` (~8 tests):
- Unsigned → signed (RSA)
- Unsigned → signed (ECDSA)
- Already signed → error without force
- Already signed → success with force
- Round-trip: sign then verify
- Re-sign with different key
- Invalid container → error
- Digest mismatch → error (tampered container)

### Step 2: Sign subcommand implementation

Create `src/jxz/cli/sign.py` with:
- `register(subparsers)` — argparse setup
- `run(args) -> int` — loads key/cert, reads file, calls `sign_container()`, writes output

Register in `src/jxz/__main__.py` (order: build, inspect, sign, verify, extract).

### Step 3: Sign subcommand tests

Create `tests/unit/test_cli_sign.py` with ~18 tests:
- **Basic**: sign unsigned container (RSA, ECDSA)
- **Output**: in-place default, custom `-o`, parent dir creation
- **Re-signing**: refuse without `--force`, succeed with `--force`
- **Round-trip**: sign then `jxz verify`
- **Errors**: missing file, missing key, cert-without-key, invalid PEM, already-signed
- **Integration**: "sign" appears in help output

### Step 4: Update documentation + version bump

- `docs/reference/cli.md` — add `jxz sign` section
- `docs/reference/api.md` — add `sign_container()` entry
- `docs/howto/use-cli.md` — add sign recipes (basic, with cert, re-sign, pipeline)
- `CHANGELOG.md` — add under `[Unreleased]`
- Version bump to 0.1.5

### Step 5: Quality gates

```bash
uv run pytest --cov=jxz --cov-report=term-missing
uv run ruff check .
uv run ruff format --check .
uv run mypy src/jxz
```

Target: 162 + ~26 = ~188 tests, coverage stays >85%.

## Edge Cases

- **In-place overwrite**: read entire file into memory first, then write — no partial-write risk since `sign_container()` returns complete bytes before we touch the file
- **Re-signing strips old signature**: the new ZIP excludes `META-INF/SIGNATURE.XML` from the source, then adds the freshly generated one
- **Container with META-INF extras**: preserved as-is during repackaging
- **Tampered container**: `sign_container()` calls `validate()` first — refuses to sign a container with bad digests
- **Encrypted private keys**: `password=None` in `load_pem_private_key` will fail with a clear error — no `--key-password` flag (same as build)

## Version

Bump to **v0.1.5** after all tests pass.
