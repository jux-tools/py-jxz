# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Read, extract, and verify .jxz signed containers."""

from __future__ import annotations

import io
import zipfile

from jxz.errors import (
    ContainerStructureError,
    DigestMismatchError,
    PathTraversalError,
)
from jxz.manifest import Manifest, compute_digest, parse


class ContainerReader:
    """Read and verify .jxz containers.

    Usage::

        reader = ContainerReader(jxz_bytes)
        reader.validate()
        report = reader.get_report()
        attachments = reader.get_attachments()
    """

    def __init__(self, data: bytes) -> None:
        """Open a .jxz container from bytes.

        Args:
            data: Complete .jxz container bytes.

        Raises:
            ContainerStructureError: If not a valid ZIP or missing required entries.
            PathTraversalError: If any ZIP entry contains path traversal.
        """
        try:
            self._zf = zipfile.ZipFile(io.BytesIO(data))
        except zipfile.BadZipFile as exc:
            msg = "Not a valid ZIP file"
            raise ContainerStructureError(msg) from exc

        names = set(self._zf.namelist())

        # Check for path traversal in all entries
        for name in names:
            if ".." in name.split("/") or name.startswith("/"):
                raise PathTraversalError(name)

        # Verify required entries
        if "META-INF/MANIFEST.MF" not in names:
            msg = "Missing required entry: META-INF/MANIFEST.MF"
            raise ContainerStructureError(msg)
        if "junit.xml" not in names:
            msg = "Missing required entry: junit.xml"
            raise ContainerStructureError(msg)

        # Parse manifest
        manifest_text = self._zf.read("META-INF/MANIFEST.MF").decode("utf-8")
        self._manifest = parse(manifest_text)

    def get_manifest(self) -> Manifest:
        """Return the parsed manifest."""
        return self._manifest

    def get_report(self) -> bytes:
        """Return the JUnit XML report bytes."""
        return self._zf.read("junit.xml")

    def get_attachments(self) -> dict[str, bytes]:
        """Return attachments as a dict of relative path to bytes.

        Keys are paths relative to ``attachments/`` (e.g. ``screenshot.png``).
        """
        prefix = "attachments/"
        result: dict[str, bytes] = {}
        for name in self._zf.namelist():
            if name.startswith(prefix) and name != prefix:
                rel = name[len(prefix) :]
                result[rel] = self._zf.read(name)
        return result

    def list_entries(self) -> list[str]:
        """Return all entry paths in the container."""
        return self._zf.namelist()

    def validate(self) -> None:
        """Validate file digests and sizes against the manifest.

        Raises:
            DigestMismatchError: If any file's SHA-256 doesn't match.
            ContainerStructureError: If a manifest entry is missing from the ZIP.
        """
        for entry in self._manifest.entries:
            name = entry["Name"]
            expected_digest = entry["SHA-256"]
            expected_size = int(entry["Size"])

            try:
                data = self._zf.read(name)
            except KeyError:
                msg = f"Manifest entry not found in archive: {name}"
                raise ContainerStructureError(msg) from None

            actual_size = len(data)
            if actual_size != expected_size:
                msg = (
                    f"Size mismatch for {name}: "
                    f"expected {expected_size}, got {actual_size}"
                )
                raise ContainerStructureError(msg)

            actual_digest = compute_digest(data)
            if actual_digest != expected_digest:
                raise DigestMismatchError(name, expected_digest, actual_digest)
