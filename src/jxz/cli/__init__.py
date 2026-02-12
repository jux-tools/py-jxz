# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Shared CLI utilities for jxz subcommands."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cryptography.x509 import Certificate

    from jxz.signing import PrivateKey


def _try_rich() -> bool:
    """Return True if rich is available."""
    try:
        import rich  # noqa: F401

        return True
    except ImportError:
        return False


def format_size(size: int) -> str:
    """Human-readable file size (e.g. '4.5 KB')."""
    if size < 1024:
        return f"{size} B"
    for unit in ("KB", "MB", "GB"):
        size_f = size / 1024
        if size_f < 1024 or unit == "GB":
            return f"{size_f:.1f} {unit}"
        size = int(size_f)
    return f"{size_f:.1f} GB"  # pragma: no cover


def load_certificate(path: str) -> Certificate:
    """Load PEM certificate from file path. Raises SystemExit on error."""
    from cryptography.x509 import load_pem_x509_certificate

    cert_path = Path(path)
    if not cert_path.is_file():
        print(f"Error: certificate file not found: {path}", file=sys.stderr)
        raise SystemExit(1)
    try:
        pem_data = cert_path.read_bytes()
        return load_pem_x509_certificate(pem_data)
    except Exception as exc:
        print(f"Error: failed to load certificate: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def load_private_key(path: str) -> PrivateKey:
    """Load PEM private key from file path. Raises SystemExit on error."""
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    key_path = Path(path)
    if not key_path.is_file():
        print(f"Error: key file not found: {path}", file=sys.stderr)
        raise SystemExit(1)
    try:
        pem_data = key_path.read_bytes()
        key = load_pem_private_key(pem_data, password=None)
        return key  # type: ignore[return-value]
    except Exception as exc:
        print(f"Error: failed to load private key: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
