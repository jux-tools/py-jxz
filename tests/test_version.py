# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Version smoke test."""

from __future__ import annotations


def test_version() -> None:
    """Package version is accessible and follows semver."""
    from jxz import __version__

    parts = __version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
