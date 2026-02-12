# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Tests for jxz.builder module."""

from __future__ import annotations

import io
import zipfile
from datetime import UTC, datetime

import pytest

from jxz.builder import ContainerBuilder
from jxz.errors import ContainerStructureError, PathTraversalError
from jxz.manifest import parse


class TestBuildMinimal:
    """Build a container with only a report."""

    def test_produces_valid_zip(self, sample_junit_xml: bytes) -> None:
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        result = builder.build(created_by="test/1.0", report_type="pytest-junit")
        assert zipfile.is_zipfile(io.BytesIO(result))

    def test_contains_required_entries(self, sample_junit_xml: bytes) -> None:
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        result = builder.build(created_by="test/1.0", report_type="pytest-junit")
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            names = zf.namelist()
        assert "META-INF/MANIFEST.MF" in names
        assert "junit.xml" in names

    def test_report_content_matches(self, sample_junit_xml: bytes) -> None:
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        result = builder.build(created_by="test/1.0", report_type="pytest-junit")
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            assert zf.read("junit.xml") == sample_junit_xml

    def test_manifest_has_required_fields(self, sample_junit_xml: bytes) -> None:
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        result = builder.build(created_by="test/1.0", report_type="pytest-junit")
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            manifest = parse(zf.read("META-INF/MANIFEST.MF").decode())
        assert manifest.main["Manifest-Version"] == "1.0"
        assert manifest.main["Created-By"] == "test/1.0"
        assert manifest.main["Report-Type"] == "pytest-junit"


class TestBuildWithAttachments:
    def test_attachment_in_zip(
        self, sample_junit_xml: bytes, sample_attachment: bytes
    ) -> None:
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        builder.add_attachment("screenshot.png", sample_attachment)
        result = builder.build(created_by="test/1.0", report_type="pytest-junit")
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            assert "attachments/screenshot.png" in zf.namelist()
            assert zf.read("attachments/screenshot.png") == sample_attachment

    def test_attachment_for_in_manifest(
        self, sample_junit_xml: bytes, sample_attachment: bytes
    ) -> None:
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        builder.add_attachment(
            "shot.png", sample_attachment, attachment_for="test_login"
        )
        result = builder.build(created_by="test/1.0", report_type="pytest-junit")
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            manifest = parse(zf.read("META-INF/MANIFEST.MF").decode())
        attachment_entry = next(
            e for e in manifest.entries if e["Name"] == "attachments/shot.png"
        )
        assert attachment_entry["Attachment-For"] == "test_login"

    def test_nested_attachment_path(self, sample_junit_xml: bytes) -> None:
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        builder.add_attachment("subdir/file.txt", b"content")
        result = builder.build(created_by="test/1.0", report_type="pytest-junit")
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            assert "attachments/subdir/file.txt" in zf.namelist()


class TestBuildWithMeta:
    def test_meta_in_zip(self, sample_junit_xml: bytes) -> None:
        meta = b'{"framework": "pytest"}'
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        builder.add_meta("pytest-metadata.json", meta)
        result = builder.build(created_by="test/1.0", report_type="pytest-junit")
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            assert "META-INF/pytest-metadata.json" in zf.namelist()
            assert zf.read("META-INF/pytest-metadata.json") == meta

    def test_meta_has_manifest_entry(self, sample_junit_xml: bytes) -> None:
        meta = b'{"framework": "pytest"}'
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        builder.add_meta("pytest-metadata.json", meta)
        result = builder.build(created_by="test/1.0", report_type="pytest-junit")
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            manifest = parse(zf.read("META-INF/MANIFEST.MF").decode())
        names = [e["Name"] for e in manifest.entries]
        assert "META-INF/pytest-metadata.json" in names


class TestBuildErrors:
    def test_no_report_raises(self) -> None:
        builder = ContainerBuilder()
        with pytest.raises(ContainerStructureError, match="No report set"):
            builder.build(created_by="test/1.0", report_type="pytest-junit")

    @pytest.mark.parametrize(
        "name",
        [
            "../etc/passwd",
            "../../secret",
            "/absolute/path",
        ],
    )
    def test_path_traversal_attachment(
        self, sample_junit_xml: bytes, name: str
    ) -> None:
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        with pytest.raises(PathTraversalError):
            builder.add_attachment(name, b"evil")

    @pytest.mark.parametrize("name", ["../etc/passwd", "/absolute"])
    def test_path_traversal_meta(self, sample_junit_xml: bytes, name: str) -> None:
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        with pytest.raises(PathTraversalError):
            builder.add_meta(name, b"evil")


class TestBuildTimestamp:
    def test_default_timestamp_is_utc(self, sample_junit_xml: bytes) -> None:
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        result = builder.build(created_by="test/1.0", report_type="pytest-junit")
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            manifest = parse(zf.read("META-INF/MANIFEST.MF").decode())
        ts = manifest.main["Timestamp"]
        assert "+" in ts or ts.endswith("Z") or "T" in ts

    def test_explicit_timestamp(self, sample_junit_xml: bytes) -> None:
        ts = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        result = builder.build(
            created_by="test/1.0", report_type="pytest-junit", timestamp=ts
        )
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            manifest = parse(zf.read("META-INF/MANIFEST.MF").decode())
        assert manifest.main["Timestamp"] == ts.isoformat()


class TestBuildIdempotent:
    def test_build_twice_produces_equivalent_archives(
        self,
        sample_junit_xml: bytes,
        fixed_timestamp: datetime,
    ) -> None:
        builder = ContainerBuilder()
        builder.set_report(sample_junit_xml)
        result1 = builder.build(
            created_by="test/1.0",
            report_type="pytest-junit",
            timestamp=fixed_timestamp,
        )
        result2 = builder.build(
            created_by="test/1.0",
            report_type="pytest-junit",
            timestamp=fixed_timestamp,
        )
        # ZIP bytes may differ (timestamps in ZIP headers), but content should match
        with (
            zipfile.ZipFile(io.BytesIO(result1)) as zf1,
            zipfile.ZipFile(io.BytesIO(result2)) as zf2,
        ):
            assert sorted(zf1.namelist()) == sorted(zf2.namelist())
            for name in zf1.namelist():
                assert zf1.read(name) == zf2.read(name)

    def test_set_report_replaces(self, sample_junit_xml: bytes) -> None:
        builder = ContainerBuilder()
        builder.set_report(b"<first/>")
        builder.set_report(sample_junit_xml)
        result = builder.build(created_by="test/1.0", report_type="pytest-junit")
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            assert zf.read("junit.xml") == sample_junit_xml
