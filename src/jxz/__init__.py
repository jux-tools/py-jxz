# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""py-jxz: Python library for .jxz signed containers.

Build, read, and verify .jxz containers as specified by the
jux-container-format specification.

Example usage:

    >>> from jxz import ContainerBuilder
    >>>
    >>> builder = ContainerBuilder()
    >>> builder.set_report(junit_xml_bytes)
    >>> builder.add_attachment("screenshot.png", png_bytes)
    >>> jxz_bytes = builder.build(
    ...     created_by="pytest-jux/0.1.0",
    ...     report_type="pytest-junit",
    ... )
"""

from __future__ import annotations

from jxz.builder import ContainerBuilder
from jxz.errors import (
    ContainerStructureError,
    DigestMismatchError,
    JxzError,
    ManifestError,
    PathTraversalError,
    SignatureError,
)
from jxz.manifest import Manifest
from jxz.reader import ContainerReader
from jxz.signing import sign_manifest, verify_signature

__version__ = "0.1.3"

__all__ = [
    "ContainerBuilder",
    "ContainerReader",
    "ContainerStructureError",
    "DigestMismatchError",
    "JxzError",
    "Manifest",
    "ManifestError",
    "PathTraversalError",
    "SignatureError",
    "__version__",
    "sign_manifest",
    "verify_signature",
]
