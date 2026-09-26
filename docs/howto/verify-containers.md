<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# How to Verify Containers

Recipes for reading, validating, and verifying `.jxz` containers with `ContainerReader`.

## Read an unsigned container

```python
from jxz import ContainerReader

with open("report.jxz", "rb") as f:
    data = f.read()

reader = ContainerReader(data)

# Access the report
report_xml = reader.get_report()

# Access attachments (dict of relative path -> bytes)
attachments = reader.get_attachments()
for name, content in attachments.items():
    print(f"{name}: {len(content)} bytes")

# Access metadata files
meta = reader.get_meta()
```

## Validate digests only

`validate()` checks that every file's SHA-256 digest and size match the manifest, without verifying any signature:

```python
from jxz import ContainerReader, DigestMismatchError, ContainerStructureError

reader = ContainerReader(data)

try:
    reader.validate()
    print("All digests match")
except DigestMismatchError as exc:
    print(f"Tampered file: {exc.entry_name}")
    print(f"  Expected: {exc.expected}")
    print(f"  Actual:   {exc.actual}")
except ContainerStructureError as exc:
    print(f"Missing file: {exc}")
```

## Verify with a certificate

`verify()` checks the signature first (if signed), then validates digests:

```python
from cryptography.x509 import load_pem_x509_certificate

cert = load_pem_x509_certificate(open("signer.pem", "rb").read())

reader = ContainerReader(data)
reader.verify(certificate=cert)
# Raises SignatureError or DigestMismatchError on failure
```

## Verify without a certificate

When no certificate is provided, the signature is verified using the key embedded in the `SIGNATURE.XML`:

```python
reader = ContainerReader(data)
reader.verify()
```

For unsigned containers, `verify()` falls through to digest validation only.

## Check if a container is signed

```python
reader = ContainerReader(data)

if reader.is_signed:
    print("Container has a signature")
    sig_xml = reader.get_signature_xml()  # raw SIGNATURE.XML bytes
else:
    print("Unsigned container")
```

## Access convenience properties

The manifest's main section fields are exposed as properties:

```python
reader = ContainerReader(data)

print(reader.created_by)  # e.g. "pytest-jux/0.1.0"
print(reader.report_type)  # e.g. "pytest-junit"
print(reader.timestamp)  # datetime object (parsed from ISO 8601)
```

## Access the full manifest

```python
reader = ContainerReader(data)
manifest = reader.get_manifest()

# Main section (dict[str, str])
print(manifest.main["Created-By"])
print(manifest.main["Timestamp"])

# Per-file entries (list[dict[str, str]])
for entry in manifest.entries:
    print(f"{entry['Name']}: {entry['Size']} bytes, SHA-256={entry['SHA-256'][:16]}...")
    if "Attachment-For" in entry:
        print(f"  Linked to test: {entry['Attachment-For']}")
```

## List all entries

```python
reader = ContainerReader(data)
for path in reader.list_entries():
    print(path)
# META-INF/MANIFEST.MF
# META-INF/SIGNATURE.XML
# junit.xml
# attachments/screenshot.png
```

## Handle verification errors

```python
from jxz import (
    ContainerReader,
    JxzError,
    SignatureError,
    DigestMismatchError,
    ContainerStructureError,
)

try:
    reader = ContainerReader(data)
    reader.verify(certificate=cert)
except SignatureError as exc:
    print(f"Signature invalid: {exc}")
except DigestMismatchError as exc:
    print(f"File tampered: {exc.entry_name}")
except ContainerStructureError as exc:
    print(f"Structural problem: {exc}")
except JxzError as exc:
    print(f"Other error: {exc}")
```
