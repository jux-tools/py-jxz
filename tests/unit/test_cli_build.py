# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Tests for jxz.cli.build subcommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from jxz.__main__ import main
from jxz.cli.build import _parse_attachment
from jxz.reader import ContainerReader

if TYPE_CHECKING:
    from pathlib import Path


class TestParseAttachment:
    def test_plain_path(self) -> None:
        path, test_id = _parse_attachment("screenshot.png")
        assert str(path) == "screenshot.png"
        assert test_id is None

    def test_path_with_test_id(self) -> None:
        path, test_id = _parse_attachment("screenshot.png:test_login")
        assert str(path) == "screenshot.png"
        assert test_id == "test_login"

    def test_path_with_directory(self) -> None:
        path, test_id = _parse_attachment("/tmp/data/screenshot.png:test_login")
        assert str(path) == "/tmp/data/screenshot.png"
        assert test_id == "test_login"

    def test_colon_in_right_side_with_slash(self) -> None:
        # Right side contains a slash, so treat entire string as path
        path, test_id = _parse_attachment("C:/Users/data/file.png")
        assert str(path) == "C:/Users/data/file.png"
        assert test_id is None

    def test_trailing_colon(self) -> None:
        # Empty right side — treat as plain path
        path, test_id = _parse_attachment("screenshot.png:")
        assert str(path) == "screenshot.png:"
        assert test_id is None


class TestBuildMinimal:
    def test_report_only(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "out.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "-o",
                str(output),
            ],
        )
        rc = main()
        assert rc == 0
        assert output.exists()
        reader = ContainerReader(output.read_bytes())
        assert reader.created_by == "test/1.0"
        assert reader.report_type == "pytest-junit"

    def test_default_output_name(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
            ],
        )
        rc = main()
        assert rc == 0
        expected = sample_junit_xml_file.with_suffix(".jxz")
        assert expected.exists()
        expected.unlink()  # cleanup

    def test_custom_output(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "custom.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "-o",
                str(output),
            ],
        )
        assert main() == 0
        assert output.exists()

    def test_parent_dir_creation(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "nested" / "dir" / "out.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "-o",
                str(output),
            ],
        )
        assert main() == 0
        assert output.exists()


class TestBuildAttachments:
    def test_single_attachment(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        sample_attachment_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "out.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "--attachment",
                str(sample_attachment_file),
                "-o",
                str(output),
            ],
        )
        assert main() == 0
        reader = ContainerReader(output.read_bytes())
        attachments = reader.get_attachments()
        assert "screenshot.png" in attachments

    def test_attachment_with_test_id(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        sample_attachment_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "out.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "--attachment",
                f"{sample_attachment_file}:test_login",
                "-o",
                str(output),
            ],
        )
        assert main() == 0
        reader = ContainerReader(output.read_bytes())
        manifest = reader.get_manifest()
        att_entry = next(
            e for e in manifest.entries if e["Name"] == "attachments/screenshot.png"
        )
        assert att_entry["Attachment-For"] == "test_login"

    def test_multiple_attachments(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        sample_attachment_file: Path,
        tmp_path: Path,
    ) -> None:
        # Create a second attachment
        att2 = tmp_path / "trace.json"
        att2.write_text('{"trace": true}')
        output = tmp_path / "out.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "--attachment",
                str(sample_attachment_file),
                "--attachment",
                str(att2),
                "-o",
                str(output),
            ],
        )
        assert main() == 0
        reader = ContainerReader(output.read_bytes())
        attachments = reader.get_attachments()
        assert "screenshot.png" in attachments
        assert "trace.json" in attachments


class TestBuildMeta:
    def test_single_meta(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        sample_meta_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "out.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "--meta",
                str(sample_meta_file),
                "-o",
                str(output),
            ],
        )
        assert main() == 0
        reader = ContainerReader(output.read_bytes())
        meta = reader.get_meta()
        assert "pytest-metadata.json" in meta

    def test_multiple_meta(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        sample_meta_file: Path,
        tmp_path: Path,
    ) -> None:
        meta2 = tmp_path / "extra.json"
        meta2.write_text('{"extra": true}')
        output = tmp_path / "out.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "--meta",
                str(sample_meta_file),
                "--meta",
                str(meta2),
                "-o",
                str(output),
            ],
        )
        assert main() == 0
        reader = ContainerReader(output.read_bytes())
        meta = reader.get_meta()
        assert "pytest-metadata.json" in meta
        assert "extra.json" in meta


class TestBuildSigning:
    def test_rsa_signing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        rsa_key_file: Path,
        cert_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "out.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "--key",
                str(rsa_key_file),
                "--cert",
                str(cert_file),
                "-o",
                str(output),
            ],
        )
        assert main() == 0
        reader = ContainerReader(output.read_bytes())
        assert reader.is_signed

    def test_ecdsa_signing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        ec_key_file: Path,
        ec_cert_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "out.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "--key",
                str(ec_key_file),
                "--cert",
                str(ec_cert_file),
                "-o",
                str(output),
            ],
        )
        assert main() == 0
        reader = ContainerReader(output.read_bytes())
        assert reader.is_signed

    def test_key_only_no_cert(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        rsa_key_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "out.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "--key",
                str(rsa_key_file),
                "-o",
                str(output),
            ],
        )
        assert main() == 0
        reader = ContainerReader(output.read_bytes())
        assert reader.is_signed

    def test_roundtrip_verify(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        rsa_key_file: Path,
        cert_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "out.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "--key",
                str(rsa_key_file),
                "--cert",
                str(cert_file),
                "-o",
                str(output),
            ],
        )
        assert main() == 0

        # Verify the built container
        monkeypatch.setattr(
            "sys.argv",
            ["jxz", "verify", "--cert", str(cert_file), str(output)],
        )
        assert main() == 0


class TestBuildTimestamp:
    def test_custom_timestamp(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "out.jxz"
        ts = "2026-01-15T10:30:00+00:00"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "--timestamp",
                ts,
                "-o",
                str(output),
            ],
        )
        assert main() == 0
        reader = ContainerReader(output.read_bytes())
        manifest = reader.get_manifest()
        assert manifest.main["Timestamp"] == ts

    def test_default_timestamp(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "out.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "-o",
                str(output),
            ],
        )
        assert main() == 0
        reader = ContainerReader(output.read_bytes())
        # Timestamp should be present (auto-generated)
        manifest = reader.get_manifest()
        assert "Timestamp" in manifest.main


class TestBuildErrors:
    def test_missing_report(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                "/nonexistent/report.xml",
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
            ],
        )
        assert main() == 1
        assert "report file not found" in capsys.readouterr().err

    def test_missing_attachment(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "--attachment",
                "/nonexistent/file.png",
                "-o",
                str(tmp_path / "out.jxz"),
            ],
        )
        assert main() == 1
        assert "attachment file not found" in capsys.readouterr().err

    def test_missing_meta(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "--meta",
                "/nonexistent/meta.json",
                "-o",
                str(tmp_path / "out.jxz"),
            ],
        )
        assert main() == 1
        assert "meta file not found" in capsys.readouterr().err

    def test_missing_key(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "--key",
                "/nonexistent/key.pem",
                "-o",
                str(tmp_path / "out.jxz"),
            ],
        )
        with pytest.raises(SystemExit):
            main()
        assert "key file not found" in capsys.readouterr().err

    def test_missing_cert(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        rsa_key_file: Path,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "--key",
                str(rsa_key_file),
                "--cert",
                "/nonexistent/cert.pem",
                "-o",
                str(tmp_path / "out.jxz"),
            ],
        )
        with pytest.raises(SystemExit):
            main()
        assert "certificate file not found" in capsys.readouterr().err

    def test_cert_without_key(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        cert_file: Path,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "--cert",
                str(cert_file),
                "-o",
                str(tmp_path / "out.jxz"),
            ],
        )
        assert main() == 1
        assert "--cert requires --key" in capsys.readouterr().err

    def test_invalid_timestamp(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "--timestamp",
                "not-a-date",
                "-o",
                str(tmp_path / "out.jxz"),
            ],
        )
        assert main() == 1
        assert "invalid timestamp" in capsys.readouterr().err

    def test_invalid_key_pem(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        bad_key = tmp_path / "bad.pem"
        bad_key.write_text("not a key")
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "--key",
                str(bad_key),
                "-o",
                str(tmp_path / "out.jxz"),
            ],
        )
        with pytest.raises(SystemExit):
            main()
        assert "failed to load private key" in capsys.readouterr().err

    def test_invalid_cert_pem(
        self,
        monkeypatch: pytest.MonkeyPatch,
        sample_junit_xml_file: Path,
        rsa_key_file: Path,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        bad_cert = tmp_path / "bad_cert.pem"
        bad_cert.write_text("not a cert")
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "--key",
                str(rsa_key_file),
                "--cert",
                str(bad_cert),
                "-o",
                str(tmp_path / "out.jxz"),
            ],
        )
        with pytest.raises(SystemExit):
            main()
        assert "failed to load certificate" in capsys.readouterr().err


class TestBuildHelp:
    def test_build_in_help(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["jxz"])
        main()
        out = capsys.readouterr().out
        assert "build" in out


class TestBuildStdout:
    def test_prints_output_path(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        sample_junit_xml_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "out.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "build",
                str(sample_junit_xml_file),
                "--created-by",
                "test/1.0",
                "--report-type",
                "pytest-junit",
                "-o",
                str(output),
            ],
        )
        assert main() == 0
        assert str(output) in capsys.readouterr().out
