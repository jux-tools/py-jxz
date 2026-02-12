# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Tests for jxz.cli.sign subcommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from jxz.__main__ import main
from jxz.reader import ContainerReader

if TYPE_CHECKING:
    from pathlib import Path


class TestSignBasic:
    def test_sign_unsigned_rsa(
        self,
        monkeypatch: pytest.MonkeyPatch,
        unsigned_jxz_file: Path,
        rsa_key_file: Path,
        cert_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "signed.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "sign",
                str(unsigned_jxz_file),
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

    def test_sign_unsigned_ecdsa(
        self,
        monkeypatch: pytest.MonkeyPatch,
        unsigned_jxz_file: Path,
        ec_key_file: Path,
        ec_cert_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "signed.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "sign",
                str(unsigned_jxz_file),
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


class TestSignOutput:
    def test_in_place_default(
        self,
        monkeypatch: pytest.MonkeyPatch,
        unsigned_jxz_file: Path,
        rsa_key_file: Path,
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "sign",
                str(unsigned_jxz_file),
                "--key",
                str(rsa_key_file),
            ],
        )
        assert main() == 0
        reader = ContainerReader(unsigned_jxz_file.read_bytes())
        assert reader.is_signed

    def test_custom_output(
        self,
        monkeypatch: pytest.MonkeyPatch,
        unsigned_jxz_file: Path,
        rsa_key_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "out.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "sign",
                str(unsigned_jxz_file),
                "--key",
                str(rsa_key_file),
                "-o",
                str(output),
            ],
        )
        assert main() == 0
        assert output.exists()

    def test_parent_dir_creation(
        self,
        monkeypatch: pytest.MonkeyPatch,
        unsigned_jxz_file: Path,
        rsa_key_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "nested" / "dir" / "signed.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "sign",
                str(unsigned_jxz_file),
                "--key",
                str(rsa_key_file),
                "-o",
                str(output),
            ],
        )
        assert main() == 0
        assert output.exists()

    def test_prints_output_path(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        unsigned_jxz_file: Path,
        rsa_key_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "signed.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "sign",
                str(unsigned_jxz_file),
                "--key",
                str(rsa_key_file),
                "-o",
                str(output),
            ],
        )
        assert main() == 0
        assert str(output) in capsys.readouterr().out


class TestSignResigning:
    def test_refuse_already_signed(
        self,
        monkeypatch: pytest.MonkeyPatch,
        signed_jxz_file: Path,
        rsa_key_file: Path,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "sign",
                str(signed_jxz_file),
                "--key",
                str(rsa_key_file),
                "-o",
                str(tmp_path / "out.jxz"),
            ],
        )
        assert main() == 1
        assert "already signed" in capsys.readouterr().err

    def test_force_resign(
        self,
        monkeypatch: pytest.MonkeyPatch,
        signed_jxz_file: Path,
        ec_key_file: Path,
        ec_cert_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "resigned.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "sign",
                str(signed_jxz_file),
                "--key",
                str(ec_key_file),
                "--cert",
                str(ec_cert_file),
                "--force",
                "-o",
                str(output),
            ],
        )
        assert main() == 0
        reader = ContainerReader(output.read_bytes())
        assert reader.is_signed


class TestSignRoundTrip:
    def test_sign_then_verify(
        self,
        monkeypatch: pytest.MonkeyPatch,
        unsigned_jxz_file: Path,
        rsa_key_file: Path,
        cert_file: Path,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "signed.jxz"
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "sign",
                str(unsigned_jxz_file),
                "--key",
                str(rsa_key_file),
                "--cert",
                str(cert_file),
                "-o",
                str(output),
            ],
        )
        assert main() == 0

        monkeypatch.setattr(
            "sys.argv",
            ["jxz", "verify", "--cert", str(cert_file), str(output)],
        )
        assert main() == 0


class TestSignErrors:
    def test_missing_file(
        self,
        monkeypatch: pytest.MonkeyPatch,
        rsa_key_file: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "sign",
                "/nonexistent/file.jxz",
                "--key",
                str(rsa_key_file),
            ],
        )
        assert main() == 1
        assert "file not found" in capsys.readouterr().err

    def test_missing_key(
        self,
        monkeypatch: pytest.MonkeyPatch,
        unsigned_jxz_file: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "sign",
                str(unsigned_jxz_file),
                "--key",
                "/nonexistent/key.pem",
            ],
        )
        with pytest.raises(SystemExit):
            main()
        assert "key file not found" in capsys.readouterr().err

    def test_missing_cert(
        self,
        monkeypatch: pytest.MonkeyPatch,
        unsigned_jxz_file: Path,
        rsa_key_file: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "sign",
                str(unsigned_jxz_file),
                "--key",
                str(rsa_key_file),
                "--cert",
                "/nonexistent/cert.pem",
            ],
        )
        with pytest.raises(SystemExit):
            main()
        assert "certificate file not found" in capsys.readouterr().err

    def test_invalid_key_pem(
        self,
        monkeypatch: pytest.MonkeyPatch,
        unsigned_jxz_file: Path,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        bad_key = tmp_path / "bad.pem"
        bad_key.write_text("not a key")
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "sign",
                str(unsigned_jxz_file),
                "--key",
                str(bad_key),
            ],
        )
        with pytest.raises(SystemExit):
            main()
        assert "failed to load private key" in capsys.readouterr().err

    def test_corrupt_container(
        self,
        monkeypatch: pytest.MonkeyPatch,
        corrupt_jxz_file: Path,
        rsa_key_file: Path,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            [
                "jxz",
                "sign",
                str(corrupt_jxz_file),
                "--key",
                str(rsa_key_file),
                "-o",
                str(tmp_path / "out.jxz"),
            ],
        )
        assert main() == 1
        assert "Error" in capsys.readouterr().err


class TestSignHelp:
    def test_sign_in_help(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["jxz"])
        main()
        out = capsys.readouterr().out
        assert "sign" in out
