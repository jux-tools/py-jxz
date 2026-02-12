# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Tests for jxz.signing module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from lxml import etree

from jxz.errors import SignatureError
from jxz.signing import sign_container, sign_manifest, verify_signature

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric import ec, rsa
    from cryptography.x509 import Certificate

SAMPLE_MANIFEST = """\
Manifest-Version: 1.0
Jux-Version: 1.0
Created-By: test/1.0
Report-Type: pytest-junit
Timestamp: 2026-01-15T10:30:00+00:00

Name: junit.xml
SHA-256: abc123
Size: 100
"""


class TestSignManifest:
    def test_returns_valid_xml(
        self,
        rsa_private_key: rsa.RSAPrivateKey,
        rsa_certificate: Certificate,
    ) -> None:
        result = sign_manifest(SAMPLE_MANIFEST, rsa_private_key, rsa_certificate)
        assert isinstance(result, bytes)
        root = etree.fromstring(result)
        assert root.tag.endswith("}Signature") or root.tag == "Signature"

    def test_rsa_signature_algorithm(
        self,
        rsa_private_key: rsa.RSAPrivateKey,
        rsa_certificate: Certificate,
    ) -> None:
        result = sign_manifest(SAMPLE_MANIFEST, rsa_private_key, rsa_certificate)
        root = etree.fromstring(result)
        ns = {"ds": "http://www.w3.org/2000/09/xmldsig#"}
        method = root.find(".//ds:SignatureMethod", ns)
        assert method is not None
        assert "rsa-sha256" in method.get("Algorithm", "").lower()

    def test_ecdsa_signature_algorithm(
        self,
        ec_private_key: ec.EllipticCurvePrivateKey,
        ec_certificate: Certificate,
    ) -> None:
        result = sign_manifest(SAMPLE_MANIFEST, ec_private_key, ec_certificate)
        root = etree.fromstring(result)
        ns = {"ds": "http://www.w3.org/2000/09/xmldsig#"}
        method = root.find(".//ds:SignatureMethod", ns)
        assert method is not None
        assert "ecdsa-sha256" in method.get("Algorithm", "").lower()

    def test_without_certificate(
        self,
        rsa_private_key: rsa.RSAPrivateKey,
    ) -> None:
        result = sign_manifest(SAMPLE_MANIFEST, rsa_private_key)
        assert isinstance(result, bytes)
        root = etree.fromstring(result)
        assert root.tag.endswith("}Signature")

    def test_with_certificate_embeds_x509(
        self,
        rsa_private_key: rsa.RSAPrivateKey,
        rsa_certificate: Certificate,
    ) -> None:
        result = sign_manifest(SAMPLE_MANIFEST, rsa_private_key, rsa_certificate)
        root = etree.fromstring(result)
        ns = {"ds": "http://www.w3.org/2000/09/xmldsig#"}
        x509_data = root.find(".//ds:KeyInfo/ds:X509Data", ns)
        assert x509_data is not None

    def test_unsupported_key_type_raises(self) -> None:
        """A non-RSA/ECDSA key should raise SignatureError."""

        class FakeKey:
            pass

        with pytest.raises(SignatureError, match="Unsupported key type"):
            sign_manifest(SAMPLE_MANIFEST, FakeKey())  # type: ignore[arg-type]


class TestVerifySignature:
    def test_round_trip_rsa(
        self,
        rsa_private_key: rsa.RSAPrivateKey,
        rsa_certificate: Certificate,
    ) -> None:
        sig = sign_manifest(SAMPLE_MANIFEST, rsa_private_key, rsa_certificate)
        verify_signature(sig, SAMPLE_MANIFEST, rsa_certificate)

    def test_round_trip_ecdsa(
        self,
        ec_private_key: ec.EllipticCurvePrivateKey,
        ec_certificate: Certificate,
    ) -> None:
        sig = sign_manifest(SAMPLE_MANIFEST, ec_private_key, ec_certificate)
        verify_signature(sig, SAMPLE_MANIFEST, ec_certificate)

    def test_round_trip_without_certificate(
        self,
        rsa_private_key: rsa.RSAPrivateKey,
    ) -> None:
        """Sign without cert, verify without cert (key-based)."""
        sig = sign_manifest(SAMPLE_MANIFEST, rsa_private_key)
        verify_signature(sig, SAMPLE_MANIFEST)

    def test_tampered_manifest_fails(
        self,
        rsa_private_key: rsa.RSAPrivateKey,
        rsa_certificate: Certificate,
    ) -> None:
        sig = sign_manifest(SAMPLE_MANIFEST, rsa_private_key, rsa_certificate)
        with pytest.raises(SignatureError):
            verify_signature(sig, SAMPLE_MANIFEST + "tampered", rsa_certificate)

    def test_tampered_signature_fails(
        self,
        rsa_private_key: rsa.RSAPrivateKey,
        rsa_certificate: Certificate,
    ) -> None:
        sig = sign_manifest(SAMPLE_MANIFEST, rsa_private_key, rsa_certificate)
        # Corrupt a byte in the signature value
        tampered = bytearray(sig)
        mid = len(tampered) // 2
        tampered[mid] ^= 0xFF
        with pytest.raises(SignatureError):
            verify_signature(bytes(tampered), SAMPLE_MANIFEST, rsa_certificate)

    def test_wrong_certificate_fails(
        self,
        rsa_private_key: rsa.RSAPrivateKey,
        rsa_certificate: Certificate,
        ec_certificate: Certificate,
    ) -> None:
        """Verifying with a different certificate should fail."""
        sig = sign_manifest(SAMPLE_MANIFEST, rsa_private_key, rsa_certificate)
        with pytest.raises(SignatureError):
            verify_signature(sig, SAMPLE_MANIFEST, ec_certificate)

    def test_malformed_xml_fails(
        self,
        rsa_certificate: Certificate,
    ) -> None:
        with pytest.raises(SignatureError):
            verify_signature(b"not xml at all", SAMPLE_MANIFEST, rsa_certificate)


class TestSignContainer:
    def test_sign_unsigned_rsa(
        self,
        sample_jxz_bytes: bytes,
        rsa_private_key: rsa.RSAPrivateKey,
        rsa_certificate: Certificate,
    ) -> None:
        result = sign_container(sample_jxz_bytes, rsa_private_key, rsa_certificate)
        from jxz.reader import ContainerReader

        reader = ContainerReader(result)
        assert reader.is_signed

    def test_sign_unsigned_ecdsa(
        self,
        sample_jxz_bytes: bytes,
        ec_private_key: ec.EllipticCurvePrivateKey,
        ec_certificate: Certificate,
    ) -> None:
        result = sign_container(sample_jxz_bytes, ec_private_key, ec_certificate)
        from jxz.reader import ContainerReader

        reader = ContainerReader(result)
        assert reader.is_signed

    def test_already_signed_raises(
        self,
        signed_jxz_bytes: bytes,
        rsa_private_key: rsa.RSAPrivateKey,
    ) -> None:
        with pytest.raises(SignatureError, match="already signed"):
            sign_container(signed_jxz_bytes, rsa_private_key)

    def test_already_signed_force(
        self,
        signed_jxz_bytes: bytes,
        rsa_private_key: rsa.RSAPrivateKey,
        rsa_certificate: Certificate,
    ) -> None:
        result = sign_container(
            signed_jxz_bytes, rsa_private_key, rsa_certificate, force=True
        )
        from jxz.reader import ContainerReader

        reader = ContainerReader(result)
        assert reader.is_signed

    def test_round_trip_sign_then_verify(
        self,
        sample_jxz_bytes: bytes,
        rsa_private_key: rsa.RSAPrivateKey,
        rsa_certificate: Certificate,
    ) -> None:
        result = sign_container(sample_jxz_bytes, rsa_private_key, rsa_certificate)
        from jxz.reader import ContainerReader

        reader = ContainerReader(result)
        reader.verify(certificate=rsa_certificate)

    def test_resign_with_different_key(
        self,
        signed_jxz_bytes: bytes,
        ec_private_key: ec.EllipticCurvePrivateKey,
        ec_certificate: Certificate,
    ) -> None:
        result = sign_container(
            signed_jxz_bytes, ec_private_key, ec_certificate, force=True
        )
        from jxz.reader import ContainerReader

        reader = ContainerReader(result)
        reader.verify(certificate=ec_certificate)

    def test_invalid_container(
        self,
        rsa_private_key: rsa.RSAPrivateKey,
    ) -> None:
        from jxz.errors import ContainerStructureError

        with pytest.raises(ContainerStructureError):
            sign_container(b"not a zip", rsa_private_key)

    def test_tampered_container(
        self,
        rsa_private_key: rsa.RSAPrivateKey,
    ) -> None:
        """Tampered container fails validation before signing."""
        import io
        import zipfile

        # Build a minimal container, then tamper with it
        from jxz.builder import ContainerBuilder
        from jxz.errors import JxzError

        builder = ContainerBuilder()
        builder.set_report(b"<testsuites/>")
        data = builder.build(created_by="test/1.0", report_type="pytest-junit")

        # Tamper: replace junit.xml content (different size triggers size check)
        buf = io.BytesIO(data)
        with zipfile.ZipFile(buf, "r") as zf_in:
            entries = {name: zf_in.read(name) for name in zf_in.namelist()}
        entries["junit.xml"] = b"<tampered/>"
        tampered_buf = io.BytesIO()
        with zipfile.ZipFile(tampered_buf, "w") as zf_out:
            for name, content in entries.items():
                zf_out.writestr(name, content)

        with pytest.raises(JxzError):
            sign_container(tampered_buf.getvalue(), rsa_private_key)
