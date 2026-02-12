<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Design Rationale

This document explains the key design decisions behind py-jxz and the `.jxz` container format.

## Why ZIP format

The `.jxz` format is a standard ZIP archive. This choice comes from the JAR (Java Archive) heritage:

- **Universal tooling**: Any ZIP utility can open a `.jxz` file for inspection. No specialized tools are needed for basic access.
- **Built-in compression**: ZIP's DEFLATE algorithm reduces file size, which matters when containers carry large attachments like screenshots or trace logs.
- **Python stdlib support**: The `zipfile` module provides reliable, well-tested ZIP handling without external dependencies.
- **Proven pattern**: JAR files, Java's standard packaging format, have used ZIP + manifest for decades. The pattern is well-understood and battle-tested.

The alternative — a custom binary format or tar-based archive — would have required more tooling without meaningful benefits.

## Why enveloping XMLDSIG

The `.jxz` signature uses enveloping XML Digital Signatures (XMLDSIG), where the signed content (the manifest text) is embedded inside the `<ds:Object>` element of the signature. The choice of XMLDSIG over simpler alternatives (like PKCS#7/CMS or JWT) reflects several constraints:

- **Self-contained signatures**: Enveloping mode means the `SIGNATURE.XML` contains both the signature and the signed content. Verification can cross-check the embedded manifest against the actual `MANIFEST.MF` file, detecting substitution attacks.
- **Standard algorithm support**: XMLDSIG supports RSA-SHA256 and ECDSA-SHA256 natively, with well-defined algorithm URIs. The `signxml` library handles the canonicalization and signature mechanics.
- **Certificate embedding**: X.509 certificates can be included in the `<ds:KeyInfo>` element, allowing verification without out-of-band key distribution.
- **Ecosystem alignment**: JUnit XML is already XML. The Jux server (Elixir) has native XML processing capabilities. Using XMLDSIG keeps the toolchain consistent.

The tradeoff is complexity — XMLDSIG canonicalization rules are notoriously tricky. We accept this cost because `signxml` abstracts it, and the alternative (inventing a custom signature scheme) would be worse.

## Why manifest-based integrity

Rather than signing each file individually, `.jxz` uses a single manifest that lists every file's SHA-256 digest and size. The signature covers only the manifest. This "manifest chaining" approach means:

- **One signature operation**: Signing and verifying are O(1) in cryptographic operations, regardless of how many files are in the container.
- **Verify without unpacking**: You can check whether the manifest signature is valid before extracting any files. Then each file's digest is checked against the manifest during extraction.
- **Bill of Materials**: The manifest serves as a complete inventory of the container's contents, which is useful for auditing and supply chain verification.
- **JAR precedent**: This is exactly how JAR signing works, and it has been reliable for decades.

The alternative — signing each file individually — would multiply the number of signature operations and complicate the format without improving security.

## Why in-memory by default

`ContainerBuilder.build()` returns `bytes` and `ContainerReader` accepts `bytes`. No temporary files are created during normal operation:

- **Atomic operations**: `build()` either produces a complete, valid container or raises an exception. There are no partial results left on disk.
- **Composability**: Callers decide what to do with the bytes — write to disk, transmit over HTTP, store in a database, or pass to another function. The library doesn't impose a filesystem layout.
- **Testing**: In-memory containers make tests fast and deterministic. No cleanup of temporary files is needed.
- **Security**: No sensitive data (private keys, signed content) is written to temporary files where it might be read by other processes.

For very large containers (hundreds of megabytes of attachments), the in-memory approach could be a concern. In practice, JUnit XML reports with a handful of attachments fit comfortably in memory. If streaming support is ever needed, it would be added as a separate API rather than changing the default.

## Why separate from py-juxlib

py-jxz is a standalone package, even though py-juxlib (the client library) is its primary consumer:

```
py-jxz                          <-- format implementation
├── used by py-juxlib            <-- client library (adds requests, metadata, etc.)
│   ├── used by pytest-jux
│   └── used by behave-jux
└── used by spooky               <-- FastAPI server
```

The separation exists because:

- **Dependency inversion**: The Jux server (spooky) needs to verify `.jxz` containers but should not depend on py-juxlib, which is a client library with `requests`, metadata detection, and other client-specific dependencies.
- **Minimal dependency footprint**: py-jxz depends only on `signxml` and `cryptography` beyond the standard library. This keeps the server's dependency tree small.
- **Single responsibility**: py-jxz does one thing — build, read, and verify `.jxz` containers. It doesn't know about HTTP, pytest, or test metadata enrichment.

If py-jxz were merged into py-juxlib, the server would either need to depend on a client library (wrong dependency direction) or duplicate the container handling code (maintenance burden).

## Security model

The `.jxz` format provides integrity and authenticity guarantees within specific boundaries.

### What `.jxz` protects against

- **Accidental corruption**: SHA-256 digests detect bit-rot, truncation, or encoding errors during transmission and storage.
- **Content tampering**: Modifying any file in the container breaks its manifest digest. Modifying the manifest breaks the signature.
- **Manifest substitution**: The enveloping signature embeds the manifest text, so replacing `MANIFEST.MF` with a different one is detected during verification.
- **ZIP slip attacks**: Path traversal in entry names (e.g., `../../etc/passwd`) is rejected at both build and read time.

### What `.jxz` does not protect against

- **Replay attacks**: A valid signed container can be submitted multiple times. Replay prevention is the server's responsibility (e.g., checking timestamps or deduplicating by digest).
- **Key compromise**: If the signing key is compromised, an attacker can produce valid signed containers. Key management (rotation, revocation) is out of scope.
- **Confidentiality**: Container contents are compressed but not encrypted. Anyone with access to the `.jxz` file can read its contents.
- **Unsigned container policy**: py-jxz does not reject unsigned containers — `verify()` succeeds for unsigned containers by only checking digests. Policy enforcement (requiring signatures) is the caller's responsibility.
