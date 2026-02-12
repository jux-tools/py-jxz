<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Sprint 2: XML Signature Support

## Goal

Add manifest signing to the builder and signature verification to the reader, completing the `.jxz` container format's security model.

## Context

Sprint 1 delivered core unsigned container operations (v0.1.1). The runtime dependencies `signxml` and `cryptography` were declared but unused. The `SignatureError` class was already defined in `errors.py`.

## Key Design Decision

**signxml enveloping mode** was chosen for XMLDSIG construction:

- The manifest is plain text (JAR format), not XML — enveloping mode accepts raw `str`/`bytes` directly
- Manifest text is embedded in a `<ds:Object>` element inside the signature
- `SIGNATURE.XML` is self-contained and self-verifiable
- Canonicalization: `exc-c14n` per spec requirement
- Algorithm detection: RSA key → RSA-SHA256, ECDSA key → ECDSA-SHA256

## Deliverables

| Item | Description | Version |
|------|-------------|---------|
| `jxz.signing` module | `sign_manifest()`, `verify_signature()`, algorithm detection | 0.1.2 |
| Builder signing | `private_key` and `certificate` params on `build()` | 0.1.2 |
| Reader verification | `is_signed` property, `verify()` method | 0.1.2 |
| Public API exports | `sign_manifest`, `verify_signature` in `jxz.__init__` | 0.1.2 |
| Test fixtures | Programmatic RSA/ECDSA key+cert generation | 0.1.2 |
| Test coverage | Unit + integration tests for all signing paths | 0.1.2 |

## Files Modified

| File | Action |
|------|--------|
| `src/jxz/signing.py` | Created |
| `src/jxz/builder.py` | Modified |
| `src/jxz/reader.py` | Modified |
| `src/jxz/__init__.py` | Modified |
| `tests/conftest.py` | Modified |
| `tests/unit/test_signing.py` | Created |
| `tests/unit/test_builder.py` | Modified |
| `tests/unit/test_reader.py` | Modified |
| `tests/integration/test_round_trip.py` | Modified |
| `CHANGELOG.md` | Updated |
| `pyproject.toml` | Version bump to 0.1.2 |

## Acceptance Criteria

- All tests pass with >85% coverage
- RSA and ECDSA signing/verification round-trips work
- Unsigned containers remain fully functional
- Tampered manifests and content are detected
- No lint or type errors
