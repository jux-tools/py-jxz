<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Getting Started with py-jxz

This tutorial walks you through the full `.jxz` container lifecycle: building a container, reading it back, signing it, and verifying it. No external files are needed — everything is self-contained.

## Prerequisites

- Python 3.11 or later
- py-jxz installed (`pip install py-jxz`)

## Step 1: Install py-jxz

```bash
pip install py-jxz
```

This installs py-jxz and its dependencies (`signxml`, `cryptography`).

## Step 2: Build an unsigned container

Create a minimal JUnit XML report and package it into a `.jxz` container:

```python
from jxz import ContainerBuilder

# A minimal JUnit XML report
report_xml = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="my_tests" tests="2" failures="0">
    <testcase classname="test_math" name="test_addition" time="0.001"/>
    <testcase classname="test_math" name="test_subtraction" time="0.002"/>
  </testsuite>
</testsuites>
"""

builder = ContainerBuilder()
builder.set_report(report_xml)

jxz_bytes = builder.build(
    created_by="tutorial/1.0",
    report_type="pytest-junit",
)

# Write to disk
with open("report.jxz", "wb") as f:
    f.write(jxz_bytes)

print(f"Built container: {len(jxz_bytes)} bytes")
```

Expected output:

```
Built container: 452 bytes
```

The result is a standard ZIP file containing `META-INF/MANIFEST.MF` and `junit.xml`.

## Step 3: Read it back

Open the container and inspect its contents:

```python
from jxz import ContainerReader

with open("report.jxz", "rb") as f:
    data = f.read()

reader = ContainerReader(data)

print(f"Created by:  {reader.created_by}")
print(f"Report type: {reader.report_type}")
print(f"Timestamp:   {reader.timestamp}")
print(f"Signed:      {reader.is_signed}")
print()

# Access the manifest
manifest = reader.get_manifest()
print(f"Files in manifest: {len(manifest.entries)}")
for entry in manifest.entries:
    print(f"  {entry['Name']} ({entry['Size']} bytes)")
```

Expected output:

```
Created by:  tutorial/1.0
Report type: pytest-junit
Timestamp:   2026-02-12T14:30:00+00:00
Signed:      False

Files in manifest: 1
  junit.xml (287 bytes)
```

## Step 4: Validate the container

Check that all file digests match the manifest:

```python
reader.validate()
print("Validation passed — all digests match")
```

If any file had been tampered with, `validate()` would raise a `DigestMismatchError`.

## Step 5: Generate a test key pair

Create an RSA key pair and a self-signed certificate for signing:

```python
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from datetime import datetime, timedelta, UTC

# Generate a 2048-bit RSA key
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# Create a self-signed certificate
subject = issuer = x509.Name(
    [
        x509.NameAttribute(NameOID.COMMON_NAME, "Tutorial Signer"),
    ]
)
certificate = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(private_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.now(UTC))
    .not_valid_after(datetime.now(UTC) + timedelta(days=365))
    .sign(private_key, hashes.SHA256())
)

print(f"Generated RSA key and certificate for: {certificate.subject}")
```

Expected output:

```
Generated RSA key and certificate for: <Name(CN=Tutorial Signer)>
```

## Step 6: Build a signed container

Use the key pair to produce a signed container:

```python
builder = ContainerBuilder()
builder.set_report(report_xml)

signed_bytes = builder.build(
    created_by="tutorial/1.0",
    report_type="pytest-junit",
    private_key=private_key,
    certificate=certificate,
)

with open("signed-report.jxz", "wb") as f:
    f.write(signed_bytes)

print(f"Built signed container: {len(signed_bytes)} bytes")
```

Expected output:

```
Built signed container: 1847 bytes
```

The signed container is larger because it includes `META-INF/SIGNATURE.XML` with the enveloping XMLDSIG signature.

## Step 7: Verify the signed container

```python
with open("signed-report.jxz", "rb") as f:
    signed_data = f.read()

reader = ContainerReader(signed_data)

print(f"Signed: {reader.is_signed}")

# Verify with the certificate
reader.verify(certificate=certificate)
print("Verification passed — signature and digests are valid")
```

Expected output:

```
Signed: True
Verification passed — signature and digests are valid
```

## Summary

You've completed the full `.jxz` lifecycle:

1. **Built** an unsigned container from a JUnit XML report
2. **Read** it back and inspected its metadata
3. **Validated** the digest integrity
4. **Generated** an RSA key pair and self-signed certificate
5. **Built** a signed container
6. **Verified** the signature and digests

## Next steps

- [How to Build Containers](../howto/build-containers.md) — recipes for attachments, metadata, and ECDSA signing
- [How to Verify Containers](../howto/verify-containers.md) — advanced verification patterns
- [How to Use the CLI](../howto/use-cli.md) — inspect, verify, and extract from the command line
- [API Reference](../reference/api.md) — full method signatures and error hierarchy
