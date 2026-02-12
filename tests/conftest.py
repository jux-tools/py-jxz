# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Shared test fixtures for py-jxz."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from jxz.builder import ContainerBuilder


@pytest.fixture()
def sample_junit_xml() -> bytes:
    """Minimal valid JUnit XML report."""
    return b"""\
<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="tests" tests="1" errors="0" failures="0">
    <testcase classname="tests.test_example" name="test_pass" time="0.001"/>
  </testsuite>
</testsuites>
"""


@pytest.fixture()
def sample_attachment() -> bytes:
    """Small PNG-like bytes for attachment tests."""
    # PNG magic bytes + minimal IHDR (not a real image, just recognizable)
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


@pytest.fixture()
def fixed_timestamp() -> datetime:
    """Fixed timestamp for deterministic tests."""
    return datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC)


@pytest.fixture()
def sample_jxz_bytes(
    sample_junit_xml: bytes,
    sample_attachment: bytes,
    fixed_timestamp: datetime,
) -> bytes:
    """Pre-built unsigned container for reader tests."""
    builder = ContainerBuilder()
    builder.set_report(sample_junit_xml)
    builder.add_attachment(
        "screenshot.png", sample_attachment, attachment_for="test_login"
    )
    return builder.build(
        created_by="test/1.0",
        report_type="pytest-junit",
        timestamp=fixed_timestamp,
    )


def _build_self_signed_cert(
    public_key: rsa.RSAPublicKey | ec.EllipticCurvePublicKey,
    private_key: rsa.RSAPrivateKey | ec.EllipticCurvePrivateKey,
    cn: str,
) -> x509.Certificate:
    """Build a self-signed certificate with signxml-required extensions."""
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    now = datetime.now(UTC)
    ski = x509.SubjectKeyIdentifier.from_public_key(public_key)
    return (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=False,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CODE_SIGNING]),
            critical=False,
        )
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("test.pyjxz.local")]),
            critical=False,
        )
        .add_extension(ski, critical=False)
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(ski),
            critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )


@pytest.fixture(scope="session")
def rsa_private_key() -> rsa.RSAPrivateKey:
    """RSA 2048-bit private key (session-scoped for speed)."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="session")
def rsa_certificate(rsa_private_key: rsa.RSAPrivateKey) -> x509.Certificate:
    """Self-signed RSA certificate."""
    return _build_self_signed_cert(
        rsa_private_key.public_key(), rsa_private_key, "test-rsa.pyjxz.local"
    )


@pytest.fixture(scope="session")
def ec_private_key() -> ec.EllipticCurvePrivateKey:
    """ECDSA P-256 private key (session-scoped for speed)."""
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture(scope="session")
def ec_certificate(ec_private_key: ec.EllipticCurvePrivateKey) -> x509.Certificate:
    """Self-signed ECDSA certificate."""
    return _build_self_signed_cert(
        ec_private_key.public_key(), ec_private_key, "test-ec.pyjxz.local"
    )


@pytest.fixture()
def sample_meta() -> bytes:
    """Sample metadata JSON bytes."""
    return b'{"framework": "pytest", "version": "8.0.0"}'


@pytest.fixture()
def jxz_bytes_with_meta(
    sample_junit_xml: bytes,
    sample_attachment: bytes,
    sample_meta: bytes,
    fixed_timestamp: datetime,
) -> bytes:
    """Pre-built unsigned container with META-INF extras for reader tests."""
    builder = ContainerBuilder()
    builder.set_report(sample_junit_xml)
    builder.add_attachment(
        "screenshot.png", sample_attachment, attachment_for="test_login"
    )
    builder.add_meta("pytest-metadata.json", sample_meta)
    return builder.build(
        created_by="test/1.0",
        report_type="pytest-junit",
        timestamp=fixed_timestamp,
    )


@pytest.fixture()
def signed_jxz_bytes(
    sample_junit_xml: bytes,
    sample_attachment: bytes,
    fixed_timestamp: datetime,
    rsa_private_key: rsa.RSAPrivateKey,
    rsa_certificate: x509.Certificate,
) -> bytes:
    """Pre-built signed container (RSA) for reader tests."""
    builder = ContainerBuilder()
    builder.set_report(sample_junit_xml)
    builder.add_attachment(
        "screenshot.png", sample_attachment, attachment_for="test_login"
    )
    return builder.build(
        created_by="test/1.0",
        report_type="pytest-junit",
        timestamp=fixed_timestamp,
        private_key=rsa_private_key,
        certificate=rsa_certificate,
    )
