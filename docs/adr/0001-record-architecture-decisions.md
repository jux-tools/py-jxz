<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# ADR-0001: Record Architecture Decisions

Date: 2026-02-12

## Status

Accepted

## Context

py-jxz requires a systematic approach to documenting significant architectural and technical decisions. As a format implementation library used by both client libraries (py-juxlib) and servers (spooky), decisions about API design, format interpretation, and dependency choices affect multiple consumers.

This is especially important for AI-assisted development, where decisions made in one session need to be understood in future sessions.

## Decision

We will use Architecture Decision Records (ADRs) to document significant architectural decisions.

**ADR Location**: All ADRs stored in `docs/adr/` directory

**ADR Format**: Following the format established by Michael Nygard:
- **Title**: Short noun phrase (ADR-NNNN: Title)
- **Status**: Proposed, Accepted, Deprecated, Superseded
- **Context**: Forces at play, including technical, business, and social
- **Decision**: The response to these forces
- **Consequences**: Resulting context after applying the decision

**Numbering**: Sequential four-digit format (0001, 0002, ...) with no gaps

**What Warrants an ADR**:
- Public API design decisions (builder, reader interfaces)
- Format interpretation choices (ambiguities in the spec)
- Dependency choices (signxml version constraints)
- Breaking changes to consumer contracts
- Security-related choices (signature algorithms, validation strictness)
- Decisions that would be costly to reverse

## Consequences

**Positive**:
- Clear record of why decisions were made
- Context preserved for future maintainers and AI assistants
- Consistent behavior across py-juxlib and spooky consumers
- Reduced repeated discussions about settled decisions

**Negative**:
- Overhead of writing and maintaining ADRs
- Risk of ADRs becoming outdated if not maintained

## References

- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) - Michael Nygard
- [ADR GitHub Organization](https://adr.github.io/)
