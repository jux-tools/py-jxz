# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""XML digital signature creation and verification for .jxz containers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from lxml import etree
from signxml import (  # type: ignore[attr-defined]
    CanonicalizationMethod,
    DigestAlgorithm,
    SignatureConfiguration,
    SignatureConstructionMethod,
    SignatureMethod,
    XMLSigner,
    XMLVerifier,
)

from jxz.errors import SignatureError

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric import ec, rsa
    from cryptography.x509 import Certificate

PrivateKey = Union["rsa.RSAPrivateKey", "ec.EllipticCurvePrivateKey"]


def _detect_signature_algorithm(private_key: PrivateKey) -> Any:
    """Detect the appropriate signature algorithm from the key type.

    Returns:
        SignatureMethod.RSA_SHA256 for RSA keys,
        SignatureMethod.ECDSA_SHA256 for ECDSA keys.

    Raises:
        SignatureError: If the key type is not supported.
    """
    from cryptography.hazmat.primitives.asymmetric import ec, rsa

    if isinstance(private_key, rsa.RSAPrivateKey):
        return SignatureMethod.RSA_SHA256
    if isinstance(private_key, ec.EllipticCurvePrivateKey):
        return SignatureMethod.ECDSA_SHA256
    msg = f"Unsupported key type: {type(private_key).__name__}"  # type: ignore[unreachable]
    raise SignatureError(msg)


def sign_manifest(
    manifest_text: str,
    private_key: PrivateKey,
    certificate: Certificate | None = None,
) -> bytes:
    """Sign manifest text using enveloping XMLDSIG.

    The manifest text is embedded inside a ``<ds:Object>`` element within
    the signature. The resulting ``SIGNATURE.XML`` is self-contained.

    Args:
        manifest_text: The MANIFEST.MF content to sign.
        private_key: RSA or ECDSA private key.
        certificate: Optional X.509 certificate to embed in the signature.

    Returns:
        SIGNATURE.XML content as UTF-8 bytes.

    Raises:
        SignatureError: If signing fails or the key type is unsupported.
    """
    from cryptography.hazmat.primitives.serialization import Encoding

    sig_algorithm = _detect_signature_algorithm(private_key)

    signer = XMLSigner(
        method=SignatureConstructionMethod.enveloping,
        signature_algorithm=sig_algorithm,
        digest_algorithm=DigestAlgorithm.SHA256,
        c14n_algorithm=CanonicalizationMethod.EXCLUSIVE_XML_CANONICALIZATION_1_0,
    )

    cert_pem: str | list[str] | None = None
    if certificate is not None:
        cert_pem = certificate.public_bytes(Encoding.PEM).decode("ascii")

    try:
        sig_element = signer.sign(
            manifest_text,
            key=private_key,
            cert=cert_pem,
        )
    except Exception as exc:
        msg = f"Failed to sign manifest: {exc}"
        raise SignatureError(msg) from exc

    result: bytes = etree.tostring(sig_element, xml_declaration=True, encoding="UTF-8")
    return result


def verify_signature(
    signature_xml: bytes,
    manifest_text: str,
    certificate: Certificate | None = None,
) -> None:
    """Verify a SIGNATURE.XML against manifest text.

    Verifies the XML digital signature and then compares the signed content
    against the expected manifest text.

    Args:
        signature_xml: The SIGNATURE.XML content.
        manifest_text: The expected MANIFEST.MF content.
        certificate: Optional X.509 certificate for verification.
            If provided, the signature is verified against this certificate.
            If None, verification uses the key embedded in the signature.

    Raises:
        SignatureError: If signature verification fails or content doesn't match.
    """
    from cryptography.hazmat.primitives.serialization import Encoding

    verifier = XMLVerifier()

    x509_cert: str | None = None
    expect_config = SignatureConfiguration(
        require_x509=certificate is not None,
        location="./",
    )
    if certificate is not None:
        x509_cert = certificate.public_bytes(Encoding.PEM).decode("ascii")

    try:
        result = verifier.verify(
            signature_xml,
            x509_cert=x509_cert,
            expect_config=expect_config,
        )
    except Exception as exc:
        msg = f"Signature verification failed: {exc}"
        raise SignatureError(msg) from exc

    # verify() with expect_references=1 (default) returns a single VerifyResult
    if isinstance(result, list):
        msg = "Unexpected multiple verification results"
        raise SignatureError(msg)

    # Extract the signed content and compare against expected manifest
    if result.signed_xml is not None:
        signed_text: str = result.signed_xml.text or ""
    else:
        signed_text = result.signed_data.decode("utf-8")

    if signed_text != manifest_text:
        msg = "Signed manifest content does not match actual manifest"
        raise SignatureError(msg)
