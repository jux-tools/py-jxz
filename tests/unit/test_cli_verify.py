# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Tests for jxz.cli.verify subcommand."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from jxz.__main__ import main

if TYPE_CHECKING:
    from pathlib import Path


class TestVerifyOk:
    def test_unsigned_passes(
        self,
        unsigned_jxz_file: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["jxz", "verify", str(unsigned_jxz_file)])
        rc = main()
        assert rc == 0
        assert "OK" in capsys.readouterr().out

    def test_signed_with_cert(
        self,
        signed_jxz_file: Path,
        cert_file: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            ["jxz", "verify", str(signed_jxz_file), "--cert", str(cert_file)],
        )
        rc = main()
        assert rc == 0
        assert "OK" in capsys.readouterr().out


class TestVerifyQuiet:
    def test_quiet_suppresses_output(
        self,
        unsigned_jxz_file: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv", ["jxz", "verify", str(unsigned_jxz_file), "--quiet"]
        )
        rc = main()
        assert rc == 0
        assert capsys.readouterr().out == ""


class TestVerifyJson:
    def test_json_ok(
        self,
        unsigned_jxz_file: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv", ["jxz", "verify", str(unsigned_jxz_file), "--json"]
        )
        rc = main()
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["status"] == "ok"

    def test_json_error_tampered(
        self,
        tampered_jxz_file: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            ["jxz", "verify", str(tampered_jxz_file), "--json"],
        )
        rc = main()
        assert rc == 1
        data = json.loads(capsys.readouterr().out)
        assert data["status"] == "error"

    def test_json_error_missing_file(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            ["jxz", "verify", "/nonexistent/file.jxz", "--json"],
        )
        rc = main()
        assert rc == 1
        data = json.loads(capsys.readouterr().out)
        assert data["status"] == "error"
        assert "not found" in data["message"]


class TestVerifyErrors:
    def test_tampered_fails(
        self,
        tampered_jxz_file: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("sys.argv", ["jxz", "verify", str(tampered_jxz_file)])
        rc = main()
        assert rc == 1

    def test_missing_file(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["jxz", "verify", "/nonexistent/file.jxz"])
        rc = main()
        assert rc == 1
        assert "not found" in capsys.readouterr().err

    def test_corrupt_file(
        self,
        corrupt_jxz_file: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["jxz", "verify", str(corrupt_jxz_file)])
        rc = main()
        assert rc == 1
        assert "Error" in capsys.readouterr().err

    def test_corrupt_file_json(
        self,
        corrupt_jxz_file: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            ["jxz", "verify", str(corrupt_jxz_file), "--json"],
        )
        rc = main()
        assert rc == 1
        data = json.loads(capsys.readouterr().out)
        assert data["status"] == "error"
