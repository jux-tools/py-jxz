# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Tests for jxz.reader module."""

from __future__ import annotations

import io
import zipfile
from typing import TYPE_CHECKING

import pytest

from jxz.errors import (
    ContainerStructureError,
    DigestMismatchError,
    PathTraversalError,
    SignatureError,
)
from jxz.manifest import Manifest, compute_digest, generate
from jxz.reader import ContainerReader

if TYPE_CHECKING:
    from cryptography.x509 import Certificate


class TestReaderInit:
    def test_open_valid_container(self, sample_jxz_bytes: bytes) -> None:
        reader = ContainerReader(sample_jxz_bytes)
        assert reader.get_manifest() is not None

    def test_not_a_zip(self) -> None:
        with pytest.raises(ContainerStructureError, match="Not a valid ZIP"):
            ContainerReader(b"this is not a zip file")

    def test_missing_manifest(self, sample_junit_xml: bytes) -> None:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("junit.xml", sample_junit_xml)
        with pytest.raises(ContainerStructureError, match=r"MANIFEST\.MF"):
            ContainerReader(buf.getvalue())

    def test_missing_junit_xml(self) -> None:
        manifest = Manifest(
            main={
                "Manifest-Version": "1.0",
                "Jux-Version": "1.0",
                "Created-By": "test/1.0",
                "Report-Type": "pytest-junit",
                "Timestamp": "2026-01-01T00:00:00Z",
            },
            entries=[],
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("META-INF/MANIFEST.MF", generate(manifest))
        with pytest.raises(ContainerStructureError, match=r"junit\.xml"):
            ContainerReader(buf.getvalue())

    def test_path_traversal_in_zip(self) -> None:
        """ZIP with path traversal entry names is rejected."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("META-INF/MANIFEST.MF", "dummy")
            zf.writestr("junit.xml", b"<xml/>")
            zf.writestr("../evil.txt", b"evil")
        with pytest.raises(PathTraversalError):
            ContainerReader(buf.getvalue())


class TestReaderReport:
    def test_get_report(self, sample_jxz_bytes: bytes, sample_junit_xml: bytes) -> None:
        reader = ContainerReader(sample_jxz_bytes)
        assert reader.get_report() == sample_junit_xml


class TestReaderAttachments:
    def test_get_attachments(
        self,
        sample_jxz_bytes: bytes,
        sample_attachment: bytes,
    ) -> None:
        reader = ContainerReader(sample_jxz_bytes)
        attachments = reader.get_attachments()
        assert "screenshot.png" in attachments
        assert attachments["screenshot.png"] == sample_attachment

    def test_no_attachments(self, sample_junit_xml: bytes) -> None:
        from jxz.builder import ContainerBuilder

        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        data = builder.build(created_by="test/1.0", report_type="pytest-junit")
        reader = ContainerReader(data)
        assert reader.get_attachments() == {}


class TestReaderListEntries:
    def test_list_entries(self, sample_jxz_bytes: bytes) -> None:
        reader = ContainerReader(sample_jxz_bytes)
        entries = reader.list_entries()
        assert "META-INF/MANIFEST.MF" in entries
        assert "junit.xml" in entries
        assert "attachments/screenshot.png" in entries


class TestReaderValidate:
    def test_intact_container_passes(self, sample_jxz_bytes: bytes) -> None:
        reader = ContainerReader(sample_jxz_bytes)
        reader.validate()  # should not raise

    def test_tampered_report_fails(self, sample_jxz_bytes: bytes) -> None:
        """Modify junit.xml content after building to break digest."""
        buf = io.BytesIO(sample_jxz_bytes)
        with zipfile.ZipFile(buf, "r") as zf_in:
            entries = {name: zf_in.read(name) for name in zf_in.namelist()}

        # Replace with same-size content to trigger digest check (not size check)
        original = entries["junit.xml"]
        tampered = bytes((b ^ 0xFF) for b in original)
        entries["junit.xml"] = tampered

        tampered_buf = io.BytesIO()
        with zipfile.ZipFile(tampered_buf, "w") as zf_out:
            for name, data in entries.items():
                zf_out.writestr(name, data)

        reader = ContainerReader(tampered_buf.getvalue())
        with pytest.raises(DigestMismatchError) as exc_info:
            reader.validate()
        assert exc_info.value.entry_name == "junit.xml"

    def test_tampered_attachment_fails(
        self,
        sample_junit_xml: bytes,
        sample_attachment: bytes,
    ) -> None:
        """Modify attachment content after building to break digest."""
        from jxz.builder import ContainerBuilder

        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        builder.add_attachment("file.bin", sample_attachment)
        original = builder.build(created_by="test/1.0", report_type="pytest-junit")

        # Tamper with the attachment
        buf = io.BytesIO(original)
        with zipfile.ZipFile(buf, "r") as zf_in:
            entries = {name: zf_in.read(name) for name in zf_in.namelist()}
        entries["attachments/file.bin"] = b"corrupted data"

        tampered_buf = io.BytesIO()
        with zipfile.ZipFile(tampered_buf, "w") as zf_out:
            for name, data in entries.items():
                zf_out.writestr(name, data)

        reader = ContainerReader(tampered_buf.getvalue())
        with pytest.raises((DigestMismatchError, ContainerStructureError)):
            reader.validate()

    def test_missing_manifest_entry_from_zip(self, sample_junit_xml: bytes) -> None:
        """Manifest references a file that doesn't exist in the ZIP."""
        report_digest = compute_digest(sample_junit_xml)
        manifest = Manifest(
            main={
                "Manifest-Version": "1.0",
                "Jux-Version": "1.0",
                "Created-By": "test/1.0",
                "Report-Type": "pytest-junit",
                "Timestamp": "2026-01-01T00:00:00Z",
            },
            entries=[
                {
                    "Name": "junit.xml",
                    "SHA-256": report_digest,
                    "Size": str(len(sample_junit_xml)),
                },
                {
                    "Name": "attachments/ghost.txt",
                    "SHA-256": "a" * 64,
                    "Size": "100",
                },
            ],
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("META-INF/MANIFEST.MF", generate(manifest))
            zf.writestr("junit.xml", sample_junit_xml)

        reader = ContainerReader(buf.getvalue())
        with pytest.raises(ContainerStructureError, match="not found in archive"):
            reader.validate()


class TestReaderIsSigned:
    def test_unsigned_container(self, sample_jxz_bytes: bytes) -> None:
        reader = ContainerReader(sample_jxz_bytes)
        assert reader.is_signed is False

    def test_signed_container(self, signed_jxz_bytes: bytes) -> None:
        reader = ContainerReader(signed_jxz_bytes)
        assert reader.is_signed is True


class TestReaderVerify:
    def test_unsigned_passes(self, sample_jxz_bytes: bytes) -> None:
        """verify() on unsigned container just runs digest validation."""
        reader = ContainerReader(sample_jxz_bytes)
        reader.verify()

    def test_signed_passes(
        self,
        signed_jxz_bytes: bytes,
        rsa_certificate: Certificate,
    ) -> None:
        reader = ContainerReader(signed_jxz_bytes)
        reader.verify(certificate=rsa_certificate)

    def test_tampered_content_fails(
        self,
        signed_jxz_bytes: bytes,
        rsa_certificate: Certificate,
    ) -> None:
        """Modify a file after signing — digest check should fail."""
        buf = io.BytesIO(signed_jxz_bytes)
        with zipfile.ZipFile(buf, "r") as zf_in:
            entries = {name: zf_in.read(name) for name in zf_in.namelist()}

        entries["junit.xml"] = b"<tampered/>"

        tampered_buf = io.BytesIO()
        with zipfile.ZipFile(tampered_buf, "w") as zf_out:
            for name, data in entries.items():
                zf_out.writestr(name, data)

        reader = ContainerReader(tampered_buf.getvalue())
        with pytest.raises((DigestMismatchError, ContainerStructureError)):
            reader.verify(certificate=rsa_certificate)

    def test_tampered_manifest_fails(
        self,
        signed_jxz_bytes: bytes,
        rsa_certificate: Certificate,
    ) -> None:
        """Modify manifest after signing — signature check should fail."""
        buf = io.BytesIO(signed_jxz_bytes)
        with zipfile.ZipFile(buf, "r") as zf_in:
            entries = {name: zf_in.read(name) for name in zf_in.namelist()}

        # Replace an existing field value (keeps manifest parseable)
        manifest = entries["META-INF/MANIFEST.MF"].decode("utf-8")
        manifest = manifest.replace("Created-By: test/1.0", "Created-By: evil/9.9")
        entries["META-INF/MANIFEST.MF"] = manifest.encode("utf-8")

        tampered_buf = io.BytesIO()
        with zipfile.ZipFile(tampered_buf, "w") as zf_out:
            for name, data in entries.items():
                zf_out.writestr(name, data)

        reader = ContainerReader(tampered_buf.getvalue())
        with pytest.raises(SignatureError):
            reader.verify(certificate=rsa_certificate)
