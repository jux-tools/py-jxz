<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# py-jxz Documentation

Documentation for py-jxz, the Python library for building, reading, and verifying `.jxz` signed containers.

Organized using the [Diátaxis](https://diataxis.fr/) documentation framework.

## Tutorials

Learning-oriented guides that walk you through complete workflows.

- [Getting Started](tutorials/getting-started.md) — Build, read, sign, and verify your first `.jxz` container

## How-to Guides

Task-oriented recipes for specific goals.

- [Build Containers](howto/build-containers.md) — Attachments, metadata, signing (RSA/ECDSA), timestamps
- [Verify Containers](howto/verify-containers.md) — Digest validation, signature verification, error handling
- [Use the CLI](howto/use-cli.md) — Inspect, verify, and extract from the command line

## Reference

Information-oriented technical descriptions.

- [API Reference](reference/api.md) — Python API: `ContainerBuilder`, `ContainerReader`, signing functions, error hierarchy
- [CLI Reference](reference/cli.md) — `jxz inspect`, `jxz verify`, `jxz extract` with all flags and exit codes
- [Quality Configuration](reference/quality-configuration.md) — Formatting standards, linting, and CI settings

## Explanation

Understanding-oriented discussion of design decisions.

- [Design Rationale](explanation/design.md) — Why ZIP, why XMLDSIG, why manifest chaining, security model

## Architecture

- [ADR Index](adr/README.md) — Architecture Decision Records
- [C4 Models](architecture/) — Architecture diagrams (Structurizr DSL)
