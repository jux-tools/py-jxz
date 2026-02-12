# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Tests for jxz.cli.inspect subcommand."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from jxz.__main__ import main

if TYPE_CHECKING:
    from pathlib import Path


class TestInspectHuman:
    def test_inspect_unsigned(
        self,
        unsigned_jxz_file: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["jxz", "inspect", str(unsigned_jxz_file)])
        rc = main()
        assert rc == 0
        out = capsys.readouterr().out
        assert "Container:" in out
        assert "Created-By:" in out
        assert "test/1.0" in out
        assert "pytest-junit" in out
        assert "Signed:" in out
        assert "junit.xml" in out

    def test_inspect_signed_rsa(
        self,
        signed_jxz_file: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["jxz", "inspect", str(signed_jxz_file)])
        rc = main()
        assert rc == 0
        out = capsys.readouterr().out
        assert "Yes (RSA-SHA256)" in out

    def test_inspect_signed_ecdsa(
        self,
        ecdsa_signed_jxz_file: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["jxz", "inspect", str(ecdsa_signed_jxz_file)])
        rc = main()
        assert rc == 0
        out = capsys.readouterr().out
        assert "Yes (ECDSA-SHA256)" in out

    def test_inspect_with_meta(
        self,
        jxz_file_with_meta: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["jxz", "inspect", str(jxz_file_with_meta)])
        rc = main()
        assert rc == 0
        out = capsys.readouterr().out
        assert "pytest-metadata.json" in out


class TestInspectJson:
    def test_json_output(
        self,
        unsigned_jxz_file: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv", ["jxz", "inspect", str(unsigned_jxz_file), "--json"]
        )
        rc = main()
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["created_by"] == "test/1.0"
        assert data["report_type"] == "pytest-junit"
        assert data["signed"] is False
        assert isinstance(data["files"], list)
        assert len(data["files"]) >= 1

    def test_json_signed_includes_signature(
        self,
        signed_jxz_file: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv", ["jxz", "inspect", str(signed_jxz_file), "--json"]
        )
        rc = main()
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["signed"] is True
        assert data["signature"] is not None


class TestInspectErrors:
    def test_missing_file(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["jxz", "inspect", "/nonexistent/file.jxz"])
        rc = main()
        assert rc == 1
        assert "not found" in capsys.readouterr().err

    def test_corrupt_file(
        self,
        corrupt_jxz_file: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["jxz", "inspect", str(corrupt_jxz_file)])
        rc = main()
        assert rc == 1
        assert "Error" in capsys.readouterr().err
