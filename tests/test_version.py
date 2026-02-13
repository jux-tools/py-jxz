# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Version smoke test."""

from __future__ import annotations

from importlib.metadata import version

import jxz


def test_version() -> None:
    """Package version is accessible and follows semver."""
    parts = jxz.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_version_matches_metadata() -> None:
    """Package __version__ should match installed metadata."""
    assert jxz.__version__ == version("py-jxz")


def test_author_exists() -> None:
    """Verify package author is defined."""
    assert hasattr(jxz, "__author__")
    assert jxz.__author__ == "Georges Martin"


def test_email_exists() -> None:
    """Verify package email is defined."""
    assert hasattr(jxz, "__email__")
    assert jxz.__email__ == "jrjsmrtn@gmail.com"
