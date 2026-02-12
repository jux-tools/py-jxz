# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Tests for jxz.cli shared utilities and __main__ dispatcher."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from jxz.__main__ import main
from jxz.cli import _try_rich, format_size, load_certificate

if TYPE_CHECKING:
    from pathlib import Path


class TestTryRich:
    def test_returns_true_when_available(self) -> None:
        # rich is installed as dev dep, so this should be True
        assert _try_rich() is True

    def test_returns_false_when_unavailable(self) -> None:
        with patch.dict("sys.modules", {"rich": None}):
            assert _try_rich() is False


class TestFormatSize:
    def test_bytes(self) -> None:
        assert format_size(0) == "0 B"
        assert format_size(512) == "512 B"
        assert format_size(1023) == "1023 B"

    def test_kilobytes(self) -> None:
        assert format_size(1024) == "1.0 KB"
        assert format_size(4608) == "4.5 KB"

    def test_megabytes(self) -> None:
        assert format_size(1024 * 1024) == "1.0 MB"
        assert format_size(5 * 1024 * 1024) == "5.0 MB"

    def test_gigabytes(self) -> None:
        assert format_size(1024 * 1024 * 1024) == "1.0 GB"
        assert format_size(3 * 1024 * 1024 * 1024) == "3.0 GB"


class TestLoadCertificate:
    def test_missing_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            load_certificate("/nonexistent/cert.pem")
        assert "not found" in capsys.readouterr().err

    def test_invalid_pem(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        bad_pem = tmp_path / "bad.pem"
        bad_pem.write_text("not a certificate")
        with pytest.raises(SystemExit):
            load_certificate(str(bad_pem))
        assert "failed to load" in capsys.readouterr().err

    def test_valid_certificate(self, cert_file: Path) -> None:
        cert = load_certificate(str(cert_file))
        assert cert is not None


class TestMainNoCommand:
    def test_no_command_prints_help(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["jxz"])
        rc = main()
        assert rc == 0
        out = capsys.readouterr().out
        assert "inspect" in out
        assert "verify" in out
        assert "extract" in out
