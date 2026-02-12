# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Tests for jxz.signing module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from lxml import etree

from jxz.errors import SignatureError
from jxz.signing import sign_manifest, verify_signature

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
