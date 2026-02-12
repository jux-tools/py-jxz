# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Error types for .jxz container operations."""

from __future__ import annotations


class JxzError(Exception):
    """Base exception for all .jxz container errors."""


class ManifestError(JxzError):
    """Error in manifest parsing or generation."""


class DigestMismatchError(JxzError):
    """SHA-256 digest does not match manifest entry."""

    def __init__(self, entry_name: str, expected: str, actual: str) -> None:
        self.entry_name = entry_name
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Digest mismatch for {entry_name}: "
            f"expected {expected}, got {actual}"
        )


class SignatureError(JxzError):
    """Error in signature creation or verification."""


class ContainerStructureError(JxzError):
    """Container is missing required entries or has invalid structure."""


class PathTraversalError(JxzError):
    """ZIP entry contains path traversal (ZIP slip)."""

    def __init__(self, entry_name: str) -> None:
        self.entry_name = entry_name
        super().__init__(f"Path traversal detected: {entry_name}")
