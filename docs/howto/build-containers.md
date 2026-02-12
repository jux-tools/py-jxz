<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# How to Build Containers

Recipes for building `.jxz` containers with `ContainerBuilder`.

## Build a basic container

A minimal container requires a JUnit XML report, a creator identifier, and a report type:

```python
from jxz import ContainerBuilder

builder = ContainerBuilder()
builder.set_report(b'<testsuites><testsuite name="suite" tests="1"><testcase name="test_pass"/></testsuite></testsuites>')

jxz_bytes = builder.build(
    created_by="my-tool/1.0",
    report_type="pytest-junit",
)

# jxz_bytes is a complete ZIP archive — write it to disk or transmit it
with open("report.jxz", "wb") as f:
    f.write(jxz_bytes)
```

## Build with attachments

Attachments are stored under `attachments/` in the container. Use `attachment_for` to link an attachment to a specific test:

```python
builder = ContainerBuilder()
builder.set_report(report_xml)

# Simple attachment
builder.add_attachment("debug.log", log_bytes)

# Attachment linked to a specific test
builder.add_attachment(
    "screenshot.png",
    png_bytes,
    attachment_for="test_login",
)

# Nested paths are allowed
builder.add_attachment("traces/api_call.json", trace_bytes)

jxz_bytes = builder.build(
    created_by="my-tool/1.0",
    report_type="pytest-junit",
)
```

## Build with metadata

Metadata files are stored under `META-INF/` alongside the manifest:

```python
import json

builder = ContainerBuilder()
builder.set_report(report_xml)

metadata = {
    "python_version": "3.12.1",
    "platform": "linux",
    "plugins": ["pytest-cov-4.1.0"],
}
builder.add_meta(
    "pytest-metadata.json",
    json.dumps(metadata).encode("utf-8"),
)

jxz_bytes = builder.build(
    created_by="pytest-jux/0.1.0",
    report_type="pytest-junit",
)
```

## Build with signing (RSA)

Generate an RSA key pair with the `cryptography` library and sign the container:

```python
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from datetime import datetime, timedelta, UTC

from jxz import ContainerBuilder

# Generate RSA key
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# Create self-signed certificate
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, "Test Signer"),
])
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

builder = ContainerBuilder()
builder.set_report(report_xml)

jxz_bytes = builder.build(
    created_by="my-tool/1.0",
    report_type="pytest-junit",
    private_key=private_key,
    certificate=certificate,
)
```

## Build with signing (ECDSA)

ECDSA keys produce smaller signatures:

```python
from cryptography.hazmat.primitives.asymmetric import ec

private_key = ec.generate_private_key(ec.SECP256R1())

# Create certificate (same pattern as RSA, using the EC key)
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

builder = ContainerBuilder()
builder.set_report(report_xml)

jxz_bytes = builder.build(
    created_by="my-tool/1.0",
    report_type="pytest-junit",
    private_key=private_key,
    certificate=certificate,
)
```

## Use a custom timestamp

By default, `build()` uses the current UTC time. To set a specific timestamp:

```python
from datetime import datetime, UTC

builder = ContainerBuilder()
builder.set_report(report_xml)

jxz_bytes = builder.build(
    created_by="my-tool/1.0",
    report_type="pytest-junit",
    timestamp=datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC),
)
```

## Handle errors

```python
from jxz import ContainerBuilder, ContainerStructureError, PathTraversalError

builder = ContainerBuilder()

# Forgetting to set a report raises ContainerStructureError
try:
    builder.build(created_by="my-tool/1.0", report_type="pytest-junit")
except ContainerStructureError as exc:
    print(f"Build failed: {exc}")
    # "No report set; call set_report() before build()"

# Path traversal in attachment names is rejected
try:
    builder.add_attachment("../../etc/passwd", b"data")
except PathTraversalError as exc:
    print(f"Rejected: {exc}")
    # "Path traversal detected: ../../etc/passwd"
```
