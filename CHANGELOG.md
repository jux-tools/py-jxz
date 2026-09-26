<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.8] - 2026-09-26

First release carrying the 0.1.7 changes to PyPI.

### Fixed

- Release workflow: pin `pypa/gh-action-pypi-publish` to v1.14.2 (was an older `release/v1`
  commit). Current hatchling writes `Metadata-Version: 2.5`, which the older action's twine
  rejected, so the 0.1.7 upload failed and nothing was published

## [0.1.7] - 2026-09-26

Tagged but never published to PyPI; see 0.1.8.

### Security

- Require `cryptography>=46.0.5` (was `>=42.0`) so an install can no longer resolve a version
  affected by CVE-2026-26007 (GHSA-r6ph-v2qm-q3c2), a subgroup attack on SECT curves caused by
  missing subgroup validation
- CI: `persist-credentials: false` on every `actions/checkout` (zizmor `artipacked`)
- Release workflow: disable `setup-uv` caching (zizmor `cache-poisoning`); reject any version that
  is not `[v]X.Y.Z[-suffix]` before it reaches a step output that later scripts expand; upgrade
  the SLSA generic generator to v2.1.0, kept referenced by tag as slsa-verifier requires
- Refresh the lockfile (26 packages)

### Fixed

- CI: track `uv.lock` and install with `uv sync --locked`, so CI runs the tool versions that were
  tested locally; ruff 0.16 formats Python code blocks in Markdown, so five docs are reformatted
- Security Scanning: audit the locked dependency set instead of the runner's Python, which held
  the toolchain's own packages and py-jxz itself (not on PyPI at the version being built, so
  `pip-audit --strict` could not pass); the SBOM job builds the SBOM from the locked runtime
  requirements and audits that same file
- Security Scanning: pin `aquasecurity/trivy-action` to v0.36.0 (Trivy v0.70.0), whose release
  exists, and `ossf/scorecard-action` to v2.4.4, whose image is on ghcr.io

## [0.1.6] - 2026-02-13

### Added

- SECURITY.md vulnerability disclosure policy
- GitHub Actions workflows: test, security, build-release
- Dependabot configuration for automated dependency updates
- PyPI Trusted Publishing via GitHub Actions OIDC

### Changed

- Migrated GitHub repository to jux-tools organization

## [0.1.5] - 2026-02-12

### Added

- `jxz sign` CLI subcommand: sign or re-sign existing `.jxz` containers
  - Required `--key` flag (RSA or ECDSA, auto-detected)
  - Optional `--cert` flag to embed certificate in signature
  - In-place signing by default, `-o` for alternate output path
  - `--force` flag to allow re-signing already-signed containers
- `sign_container()` library function in `jxz.signing`: programmatic signing of existing containers
  - Validates digests before signing (refuses tampered containers)
  - Supports re-signing with `force=True`

## [0.1.4] - 2026-02-12

### Added

- `jxz build` CLI subcommand: assemble `.jxz` containers from the command line
  - Required `--created-by` and `--report-type` flags
  - Repeatable `--attachment PATH[:TEST_ID]` and `--meta FILE` flags
  - `--key` and `--cert` flags for RSA/ECDSA signing
  - `--timestamp` for reproducible builds, `-o` for custom output path
  - Creates parent directories for output path automatically
- `load_private_key()` CLI utility in `jxz.cli` (mirrors existing `load_certificate()`)
- Diátaxis documentation framework populated with content:
  - Tutorial: getting-started walkthrough (build, read, sign, verify lifecycle)
  - How-to guides: build containers, verify containers, use the CLI
  - Reference: Python API and CLI reference
  - Explanation: design rationale (ZIP format, XMLDSIG, manifest chaining, security model)
  - Documentation index (`docs/README.md`)

## [0.1.3] - 2026-02-12

### Added

- `ContainerReader.get_meta()`: return META-INF extras (excluding MANIFEST.MF and SIGNATURE.XML) as a dict
- `ContainerReader.get_signature_xml()`: return raw SIGNATURE.XML bytes, or None if unsigned
- `ContainerReader.created_by` property: producer tool identifier from manifest
- `ContainerReader.report_type` property: report dialect from manifest
- `ContainerReader.timestamp` property: parsed ISO 8601 datetime from manifest
- `python -m jxz` CLI with three subcommands:
  - `inspect`: display container metadata, file listing, and signature status (human-readable and `--json`)
  - `verify`: verify container integrity and signatures (`--cert`, `--quiet`, `--json`)
  - `extract`: extract container contents to disk (`--output`, `--report-only`, `--attachments-only`)
- `jxz` console script entry point via `[project.scripts]`
- Optional `cli` extra with `rich>=13.0` for enhanced terminal output
- CLI test suite covering all three subcommands

## [0.1.2] - 2026-02-12

### Added

- `jxz.signing` module: `sign_manifest()` and `verify_signature()` for XML digital signature creation and verification using signxml (enveloping XMLDSIG with exc-c14n)
- `ContainerBuilder.build()` now accepts `private_key` and `certificate` parameters to produce signed containers with `META-INF/SIGNATURE.XML`
- `ContainerReader.is_signed` property to check for signature presence
- `ContainerReader.verify()` method: validates signature (if present) then digests, following spec verification order
- Support for both RSA-SHA256 and ECDSA-SHA256 signature algorithms (auto-detected from key type)
- Signing and verification test suite with programmatic key/certificate generation

## [0.1.1] - 2026-02-12

### Added

- `jxz.manifest` module: `Manifest` dataclass, `generate()`, `parse()`, `compute_digest()` for JAR-style manifest handling
- `jxz.builder` module: `ContainerBuilder` class for assembling unsigned `.jxz` containers from JUnit XML reports, attachments, and metadata
- `jxz.reader` module: `ContainerReader` class for extracting and validating `.jxz` containers with SHA-256 digest verification
- Public API exports: `ContainerBuilder`, `ContainerReader`, `Manifest`, and all error classes
- Comprehensive test suite: unit tests for manifest, builder, reader; integration round-trip tests
- Path traversal (ZIP slip) protection in both builder and reader

## [0.1.0] - 2026-02-12

### Added

- Initial project structure with hatchling build system
- Package skeleton: `jxz.builder`, `jxz.manifest`, `jxz.reader`, `jxz.errors`
- Error hierarchy: `JxzError`, `ManifestError`, `DigestMismatchError`, `SignatureError`, `ContainerStructureError`, `PathTraversalError`
- Foundational ADRs (0001-0003)
- Development tooling: ruff, mypy, pytest, pre-commit hooks
- Apache-2.0 license with SPDX headers
