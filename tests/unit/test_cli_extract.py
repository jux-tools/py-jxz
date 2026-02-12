# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Tests for jxz.cli.extract subcommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from jxz.__main__ import main

if TYPE_CHECKING:
    from pathlib import Path


class TestExtract:
    def test_extract_to_dir(
        self,
        unsigned_jxz_file: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        out_dir = tmp_path / "out"
        monkeypatch.setattr(
            "sys.argv",
            ["jxz", "extract", str(unsigned_jxz_file), "--output", str(out_dir)],
        )
        rc = main()
        assert rc == 0
        assert (out_dir / "junit.xml").is_file()
        assert (out_dir / "attachments" / "screenshot.png").is_file()
        stdout = capsys.readouterr().out
        assert "junit.xml" in stdout
        assert "screenshot.png" in stdout

    def test_report_only(
        self,
        unsigned_jxz_file: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        out_dir = tmp_path / "report_only"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "extract",
                str(unsigned_jxz_file),
                "--output",
                str(out_dir),
                "--report-only",
            ],
        )
        rc = main()
        assert rc == 0
        assert (out_dir / "junit.xml").is_file()
        assert not (out_dir / "attachments").exists()

    def test_attachments_only(
        self,
        unsigned_jxz_file: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        out_dir = tmp_path / "att_only"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "extract",
                str(unsigned_jxz_file),
                "--output",
                str(out_dir),
                "--attachments-only",
            ],
        )
        rc = main()
        assert rc == 0
        assert not (out_dir / "junit.xml").exists()
        assert (out_dir / "attachments" / "screenshot.png").is_file()

    def test_extract_with_meta(
        self,
        jxz_file_with_meta: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        out_dir = tmp_path / "with_meta"
        monkeypatch.setattr(
            "sys.argv",
            ["jxz", "extract", str(jxz_file_with_meta), "--output", str(out_dir)],
        )
        rc = main()
        assert rc == 0
        assert (out_dir / "META-INF" / "pytest-metadata.json").is_file()
        stdout = capsys.readouterr().out
        assert "pytest-metadata.json" in stdout


class TestExtractErrors:
    def test_tampered_refuses(
        self,
        tampered_jxz_file: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        out_dir = tmp_path / "tampered_out"
        monkeypatch.setattr(
            "sys.argv",
            ["jxz", "extract", str(tampered_jxz_file), "--output", str(out_dir)],
        )
        rc = main()
        assert rc == 1
        assert "integrity" in capsys.readouterr().err

    def test_missing_file(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["jxz", "extract", "/nonexistent/file.jxz"])
        rc = main()
        assert rc == 1
        assert "not found" in capsys.readouterr().err

    def test_corrupt_file(
        self,
        corrupt_jxz_file: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            ["jxz", "extract", str(corrupt_jxz_file), "--output", str(tmp_path / "x")],
        )
        rc = main()
        assert rc == 1
        assert "Error" in capsys.readouterr().err
