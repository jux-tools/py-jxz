# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Tests for jxz.cli.verify subcommand."""

from __future__ import annotations

import io
import json
import zipfile
from typing import TYPE_CHECKING

import pytest

from jxz.__main__ import main

if TYPE_CHECKING:
    from pathlib import Path

    from cryptography.x509 import Certificate


@pytest.fixture()
def unsigned_jxz_file(
    tmp_path: Path,
    sample_jxz_bytes: bytes,
) -> Path:
    p = tmp_path / "unsigned.jxz"
    p.write_bytes(sample_jxz_bytes)
    return p


@pytest.fixture()
def signed_jxz_file(
    tmp_path: Path,
    signed_jxz_bytes: bytes,
) -> Path:
    p = tmp_path / "signed.jxz"
    p.write_bytes(signed_jxz_bytes)
    return p


@pytest.fixture()
def cert_file(
    tmp_path: Path,
    rsa_certificate: Certificate,
) -> Path:
    from cryptography.hazmat.primitives.serialization import Encoding

    p = tmp_path / "cert.pem"
    p.write_bytes(rsa_certificate.public_bytes(Encoding.PEM))
    return p


@pytest.fixture()
def tampered_jxz_file(
    tmp_path: Path,
    sample_jxz_bytes: bytes,
) -> Path:
    """Container with tampered junit.xml content."""
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

    def test_json_error(
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
