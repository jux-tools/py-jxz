<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-02-12

### Added

- Initial project structure with hatchling build system
- Package skeleton: `jxz.builder`, `jxz.manifest`, `jxz.reader`, `jxz.errors`
- Error hierarchy: `JxzError`, `ManifestError`, `DigestMismatchError`, `SignatureError`, `ContainerStructureError`, `PathTraversalError`
- Foundational ADRs (0001-0003)
- Development tooling: ruff, mypy, pytest, pre-commit hooks
- Apache-2.0 license with SPDX headers
