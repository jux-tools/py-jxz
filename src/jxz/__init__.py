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
    >>> jxz_bytes = builder.build()
"""

from __future__ import annotations

__version__ = "0.1.0"
