<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# py-jxz

Python library for building, reading, and verifying `.jxz` signed containers.

The `.jxz` format packages signed JUnit XML test reports with attachments for secure transmission, as specified by the [jux-container-format](https://github.com/jux-tools/jux-container-format) specification.

## Features

- **Build** `.jxz` containers from JUnit XML reports and attachments
- **Read** and extract `.jxz` containers with digest validation
- **Sign** containers with detached XMLDSIG signatures
- **Verify** signatures and SHA-256 manifest digests
- **Minimal dependencies**: `signxml` + `cryptography` beyond stdlib

## Installation

```bash
pip install py-jxz
```

## Quick Start

### Build a container

```python
from jxz import ContainerBuilder

builder = ContainerBuilder()
builder.set_report(junit_xml_bytes)
builder.add_attachment("screenshots/login.png", png_bytes)

# Unsigned
jxz_bytes = builder.build()

# Signed
jxz_bytes = builder.build(private_key=key, certificate=cert)
```

### Read and verify a container

```python
from jxz import ContainerReader

reader = ContainerReader(jxz_bytes)
reader.verify()
report = reader.get_report()
attachments = reader.get_attachments()
```

## Documentation

- [Format Specification](https://github.com/jux-tools/jux-container-format)
- [Changelog](CHANGELOG.md)

## Related Projects

| Project | Description |
|---------|-------------|
| [jux-container-format](https://github.com/jux-tools/jux-container-format) | `.jxz` format specification |
| [py-juxlib](https://github.com/jux-tools/py-juxlib) | Jux client library (depends on py-jxz) |
| [jux-openapi](https://github.com/jux-tools/jux-openapi) | Jux REST API specification |

## License

Apache-2.0
