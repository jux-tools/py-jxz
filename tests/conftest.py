# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Shared test fixtures for py-jxz."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

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
