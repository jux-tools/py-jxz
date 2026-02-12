# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Integration tests: build → read → validate round-trips."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from jxz.builder import ContainerBuilder
from jxz.reader import ContainerReader

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric import ec, rsa
    from cryptography.x509 import Certificate


@pytest.mark.integration()
class TestRoundTrip:
    def test_report_only(self, sample_junit_xml: bytes) -> None:
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        jxz_bytes = builder.build(created_by="test/1.0", report_type="pytest-junit")

        reader = ContainerReader(jxz_bytes)
        reader.validate()
        assert reader.get_report() == sample_junit_xml

    def test_report_with_attachments(
        self,
        sample_junit_xml: bytes,
        sample_attachment: bytes,
    ) -> None:
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        builder.add_attachment(
            "screenshot.png", sample_attachment, attachment_for="test_login"
        )
        builder.add_attachment("trace.json", b'{"trace": []}')
        jxz_bytes = builder.build(created_by="test/1.0", report_type="pytest-junit")

        reader = ContainerReader(jxz_bytes)
        reader.validate()
        assert reader.get_report() == sample_junit_xml
        attachments = reader.get_attachments()
        assert attachments["screenshot.png"] == sample_attachment
        assert attachments["trace.json"] == b'{"trace": []}'

    def test_report_with_attachments_and_meta(
        self,
        sample_junit_xml: bytes,
        sample_attachment: bytes,
    ) -> None:
        meta_json = b'{"framework": "pytest", "version": "8.0"}'
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        builder.add_attachment("shot.png", sample_attachment)
        builder.add_meta("pytest-metadata.json", meta_json)
        jxz_bytes = builder.build(
            created_by="pytest-jux/0.1.0", report_type="pytest-junit"
        )

        reader = ContainerReader(jxz_bytes)
        reader.validate()
        assert reader.get_report() == sample_junit_xml
        assert reader.get_attachments()["shot.png"] == sample_attachment

        # Verify meta is in the ZIP
        entries = reader.list_entries()
        assert "META-INF/pytest-metadata.json" in entries

        # Verify manifest metadata
        manifest = reader.get_manifest()
        assert manifest.main["Created-By"] == "pytest-jux/0.1.0"
        meta_entry = next(
            e for e in manifest.entries if e["Name"] == "META-INF/pytest-metadata.json"
        )
        assert int(meta_entry["Size"]) == len(meta_json)

    def test_byte_for_byte_fidelity(self, sample_junit_xml: bytes) -> None:
        """Extracted content matches original input byte-for-byte."""
        attachment_data = bytes(range(256))
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        builder.add_attachment("binary.bin", attachment_data)
        ts = datetime(2026, 3, 1, 0, 0, 0, tzinfo=UTC)
        jxz_bytes = builder.build(
            created_by="test/1.0", report_type="pytest-junit", timestamp=ts
        )

        reader = ContainerReader(jxz_bytes)
        reader.validate()
        assert reader.get_report() == sample_junit_xml
        assert reader.get_attachments()["binary.bin"] == attachment_data


@pytest.mark.integration()
class TestSignedRoundTrip:
    def test_rsa_signed(
        self,
        sample_junit_xml: bytes,
        rsa_private_key: rsa.RSAPrivateKey,
        rsa_certificate: Certificate,
    ) -> None:
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        jxz_bytes = builder.build(
            created_by="test/1.0",
            report_type="pytest-junit",
            private_key=rsa_private_key,
            certificate=rsa_certificate,
        )

        reader = ContainerReader(jxz_bytes)
        assert reader.is_signed
        reader.verify(certificate=rsa_certificate)
        assert reader.get_report() == sample_junit_xml

    def test_ecdsa_signed(
        self,
        sample_junit_xml: bytes,
        ec_private_key: ec.EllipticCurvePrivateKey,
        ec_certificate: Certificate,
    ) -> None:
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        jxz_bytes = builder.build(
            created_by="test/1.0",
            report_type="pytest-junit",
            private_key=ec_private_key,
            certificate=ec_certificate,
        )

        reader = ContainerReader(jxz_bytes)
        assert reader.is_signed
        reader.verify(certificate=ec_certificate)
        assert reader.get_report() == sample_junit_xml

    def test_signed_with_attachments_and_meta(
        self,
        sample_junit_xml: bytes,
        sample_attachment: bytes,
        rsa_private_key: rsa.RSAPrivateKey,
        rsa_certificate: Certificate,
    ) -> None:
        meta_json = b'{"framework": "pytest"}'
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        builder.add_attachment(
            "screenshot.png", sample_attachment, attachment_for="test_login"
        )
        builder.add_meta("pytest-metadata.json", meta_json)
        jxz_bytes = builder.build(
            created_by="pytest-jux/0.1.0",
            report_type="pytest-junit",
            private_key=rsa_private_key,
            certificate=rsa_certificate,
        )

        reader = ContainerReader(jxz_bytes)
        assert reader.is_signed
        reader.verify(certificate=rsa_certificate)
        assert reader.get_report() == sample_junit_xml
        assert reader.get_attachments()["screenshot.png"] == sample_attachment

    def test_unsigned_verifiable(self, sample_junit_xml: bytes) -> None:
        """Unsigned container passes verify() (no signature to check)."""
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        jxz_bytes = builder.build(created_by="test/1.0", report_type="pytest-junit")

        reader = ContainerReader(jxz_bytes)
        assert not reader.is_signed
        reader.verify()
