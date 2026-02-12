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


@pytest.fixture()
def unsigned_jxz_file(
    tmp_path: Path,
    sample_jxz_bytes: bytes,
) -> Path:
    """Write unsigned container to a temp file."""
    p = tmp_path / "unsigned.jxz"
    p.write_bytes(sample_jxz_bytes)
    return p


@pytest.fixture()
def signed_jxz_file(
    tmp_path: Path,
    signed_jxz_bytes: bytes,
) -> Path:
    """Write signed container to a temp file."""
    p = tmp_path / "signed.jxz"
    p.write_bytes(signed_jxz_bytes)
    return p


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

    def test_inspect_signed(
        self,
        signed_jxz_file: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["jxz", "inspect", str(signed_jxz_file)])
        rc = main()
        assert rc == 0
        out = capsys.readouterr().out
        assert "Yes" in out


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
