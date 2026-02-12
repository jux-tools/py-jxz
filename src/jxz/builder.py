# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Build .jxz signed containers from JUnit XML reports and attachments."""

from __future__ import annotations

import io
import zipfile
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from jxz.errors import ContainerStructureError, PathTraversalError
from jxz.manifest import Manifest, compute_digest, generate

if TYPE_CHECKING:
    from cryptography.x509 import Certificate

    from jxz.signing import PrivateKey


def _check_path_traversal(name: str) -> None:
    """Raise PathTraversalError if name contains path traversal."""
    if ".." in name.split("/") or name.startswith("/"):
        raise PathTraversalError(name)


class ContainerBuilder:
    """Build .jxz containers from JUnit XML reports and attachments.

    Usage::

        builder = ContainerBuilder()
        builder.set_report(junit_xml_bytes)
        builder.add_attachment("screenshot.png", png_bytes)
        jxz_bytes = builder.build(
            created_by="pytest-jux/0.1.0",
            report_type="pytest-junit",
        )
    """

    def __init__(self) -> None:
        self._report: bytes | None = None
        self._attachments: dict[str, tuple[bytes, str | None]] = {}
        self._meta: dict[str, bytes] = {}

    def set_report(self, data: bytes) -> None:
        """Set or replace the JUnit XML report."""
        self._report = data

    def add_attachment(
        self,
        name: str,
        data: bytes,
        *,
        attachment_for: str | None = None,
    ) -> None:
        """Add an attachment to the container.

        Args:
            name: Relative path under ``attachments/`` (e.g. ``screenshot.png``).
            data: Attachment content.
            attachment_for: Optional test identifier this attachment belongs to.

        Raises:
            PathTraversalError: If name contains ``..`` or starts with ``/``.
        """
        _check_path_traversal(name)
        self._attachments[name] = (data, attachment_for)

    def add_meta(self, name: str, data: bytes) -> None:
        """Add a metadata file under ``META-INF/``.

        Args:
            name: Filename (e.g. ``pytest-metadata.json``).
            data: File content.

        Raises:
            PathTraversalError: If name contains ``..`` or starts with ``/``.
        """
        _check_path_traversal(name)
        self._meta[name] = data

    def build(
        self,
        *,
        created_by: str,
        report_type: str,
        timestamp: datetime | None = None,
        private_key: PrivateKey | None = None,
        certificate: Certificate | None = None,
    ) -> bytes:
        """Build the .jxz container and return ZIP bytes.

        Args:
            created_by: Tool identifier (e.g. ``pytest-jux/0.1.0``).
            report_type: Report type (e.g. ``pytest-junit``).
            timestamp: Optional timestamp; defaults to now (UTC).
            private_key: Optional RSA or ECDSA key for signing the manifest.
            certificate: Optional X.509 certificate to embed in the signature.

        Returns:
            Complete .jxz container as bytes.

        Raises:
            ContainerStructureError: If no report has been set.
            SignatureError: If signing fails.
        """
        if self._report is None:
            msg = "No report set; call set_report() before build()"
            raise ContainerStructureError(msg)

        if timestamp is None:
            timestamp = datetime.now(UTC)

        # Collect all files: path -> data
        files: dict[str, bytes] = {"junit.xml": self._report}
        for name, (data, _) in self._attachments.items():
            files[f"attachments/{name}"] = data
        for name, data in self._meta.items():
            files[f"META-INF/{name}"] = data

        # Build manifest entries
        entries: list[dict[str, str]] = []
        for path, data in files.items():
            entry: dict[str, str] = {
                "Name": path,
                "SHA-256": compute_digest(data),
                "Size": str(len(data)),
            }
            # Add Attachment-For if this is an attachment with the field set
            if path.startswith("attachments/"):
                rel_name = path[len("attachments/") :]
                if rel_name in self._attachments:
                    _, attachment_for = self._attachments[rel_name]
                    if attachment_for is not None:
                        entry["Attachment-For"] = attachment_for
            entries.append(entry)

        manifest = Manifest(
            main={
                "Manifest-Version": "1.0",
                "Jux-Version": "1.0",
                "Created-By": created_by,
                "Report-Type": report_type,
                "Timestamp": timestamp.isoformat(),
            },
            entries=entries,
        )
        manifest_text = generate(manifest)

        # Sign manifest if a private key was provided
        signature_xml: bytes | None = None
        if private_key is not None:
            from jxz.signing import sign_manifest

            signature_xml = sign_manifest(manifest_text, private_key, certificate)

        # Assemble ZIP
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("META-INF/MANIFEST.MF", manifest_text)
            if signature_xml is not None:
                zf.writestr("META-INF/SIGNATURE.XML", signature_xml)
            for path, data in files.items():
                zf.writestr(path, data)

        return buf.getvalue()
