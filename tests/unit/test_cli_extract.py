# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Tests for jxz.cli.extract subcommand."""

from __future__ import annotations

import io
import zipfile
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from jxz.__main__ import main


@pytest.fixture()
def unsigned_jxz_file(
    tmp_path: Path,
    sample_jxz_bytes: bytes,
) -> Path:
    p = tmp_path / "unsigned.jxz"
    p.write_bytes(sample_jxz_bytes)
    return p


@pytest.fixture()
def tampered_jxz_file(
    tmp_path: Path,
    sample_jxz_bytes: bytes,
) -> Path:
    buf = io.BytesIO(sample_jxz_bytes)
    with zipfile.ZipFile(buf, "r") as zf_in:
        entries = {name: zf_in.read(name) for name in zf_in.namelist()}
    entries["junit.xml"] = b"<tampered/>"
    tampered_buf = io.BytesIO()
    with zipfile.ZipFile(tampered_buf, "w") as zf_out:
        for name, data in entries.items():
            zf_out.writestr(name, data)
    p = tmp_path / "tampered.jxz"
    p.write_bytes(tampered_buf.getvalue())
    return p


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
