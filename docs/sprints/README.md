<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Sprint Documentation

This directory contains sprint planning and retrospective documents for py-jxz.

## Current Status

- **Latest Release**: v0.1.5
- **Current Sprint**: Sprint 5 (completed)

## Sprint Index

| Sprint | Version | Date | Status | Plan | Retrospective |
|--------|---------|------|--------|------|---------------|
| 1 | v0.1.1 | 2026-02-12 | Done | [plan](sprint-01-plan.md) | [retro](sprint-01-retrospective.md) |
| 2 | v0.1.2 | 2026-02-12 | Done | [plan](sprint-02-plan.md) | [retro](sprint-02-retrospective.md) |
| 3 | v0.1.3 | 2026-02-12 | Done | [plan](sprint-03-plan.md) | [retro](sprint-03-retrospective.md) |
| 4 | v0.1.4 | 2026-02-12 | Done | [plan](sprint-04-plan.md) | [retro](sprint-04-retrospective.md) |
| 5 | v0.1.5 | 2026-02-12 | Done | [plan](sprint-05-plan.md) | [retro](sprint-05-retrospective.md) |
| 6 | v0.1.6 | — | Proposed | [proposal](sprint-06-proposal.md) | — |

## Roadmap Summary

| Sprint | Focus | Modules |
|--------|-------|---------|
| 1 | Core container operations | manifest, builder, reader |
| 2 | Signing and verification | XMLDSIG enveloping, certificate handling |
| 3 | API polish & CLI tooling | reader accessors, inspect/verify/extract |
| 4 | `jxz build` CLI & utilities | build subcommand, load_private_key |
| 5 | `jxz sign` CLI & library | sign subcommand, sign_container() |
| 6 | File-backed I/O | path-based builder, from_file reader, file-to-file signing |

## Story Point Reference

| Points | Complexity | Duration | Example |
|--------|------------|----------|---------|
| 1 | Trivial | < 2 hours | Config change, small fix |
| 2 | Simple | 2-4 hours | Single function |
| 3 | Medium | 4-8 hours | Multiple functions |
| 5 | Complex | 1-2 days | New module |
| 8 | Very Complex | 2-3 days | Major feature |

## Related Documentation

- [ADR-0002](../adr/0002-adopt-development-best-practices.md) - Sprint methodology
- [CHANGELOG.md](../../CHANGELOG.md) - Version history
