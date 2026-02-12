# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""JAR-style manifest generation and parsing for .jxz containers."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import TypedDict


class ManifestMainSection(TypedDict, total=False):
    """Main section fields of a .jxz manifest.

    Required: Manifest-Version, Jux-Version, Created-By, Report-Type, Timestamp.
    Additional properties are allowed per the schema.
    """


class ManifestEntry(TypedDict, total=False):
    """Per-file entry in a .jxz manifest.

    Required: Name, SHA-256, Size.
    Optional: Attachment-For.
    Additional properties are allowed per the schema.
    """


@dataclass
class Manifest:
    """Parsed .jxz manifest with main section and per-file entries."""

    main: dict[str, str] = field(default_factory=dict)
    entries: list[dict[str, str]] = field(default_factory=list)


def generate(manifest: Manifest) -> str:
    """Serialize a Manifest to JAR-style text.

    Format:
    - Key-value pairs separated by ```: ``` (colon-space)
    - Sections separated by blank lines
    - Main section first, then per-entry sections
    - Trailing newline after last section
    """
    lines: list[str] = []

    # Main section
    for key, value in manifest.main.items():
        lines.append(f"{key}: {value}")
    lines.append("")  # blank line after main section

    # Per-entry sections
    for entry in manifest.entries:
        for key, value in entry.items():
            lines.append(f"{key}: {value}")
        lines.append("")  # blank line after each entry

    return "\n".join(lines)


def parse(text: str) -> Manifest:
    """Parse JAR-style manifest text into a Manifest.

    Raises:
        ManifestError: If the text is malformed or missing required fields.
    """
    from jxz.errors import ManifestError

    if not text.strip():
        msg = "Empty manifest"
        raise ManifestError(msg)

    sections: list[dict[str, str]] = []
    current: dict[str, str] = {}

    for line in text.splitlines():
        if not line:
            # Blank line separates sections
            if current:
                sections.append(current)
                current = {}
        else:
            sep = line.find(": ")
            if sep == -1:
                msg = f"Malformed manifest line: {line!r}"
                raise ManifestError(msg)
            key = line[:sep]
            value = line[sep + 2 :]
            current[key] = value

    # Handle last section if no trailing blank line
    if current:
        sections.append(current)

    if not sections:
        msg = "No sections found in manifest"
        raise ManifestError(msg)

    main = sections[0]
    entries = sections[1:]

    # Validate required main section fields
    required_main = {
        "Manifest-Version",
        "Jux-Version",
        "Created-By",
        "Report-Type",
        "Timestamp",
    }
    missing = required_main - main.keys()
    if missing:
        msg = f"Missing required main section fields: {', '.join(sorted(missing))}"
        raise ManifestError(msg)

    # Validate required entry fields
    required_entry = {"Name", "SHA-256", "Size"}
    for i, entry in enumerate(entries):
        entry_missing = required_entry - entry.keys()
        if entry_missing:
            name = entry.get("Name", f"entry #{i}")
            msg = (
                f"Missing required fields in {name}: {', '.join(sorted(entry_missing))}"
            )
            raise ManifestError(msg)

    return Manifest(main=main, entries=entries)


def compute_digest(data: bytes) -> str:
    """Compute SHA-256 hex digest of data."""
    return hashlib.sha256(data).hexdigest()
