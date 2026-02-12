<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
