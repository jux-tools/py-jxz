# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Sign subcommand: sign or re-sign an existing .jxz container."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from jxz.cli import load_certificate, load_private_key
from jxz.errors import JxzError

if TYPE_CHECKING:
    import argparse


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the sign subcommand."""
    parser = subparsers.add_parser("sign", help="sign a .jxz container")
    parser.add_argument("file", help="path to .jxz file")
    parser.add_argument("--key", required=True, help="private key PEM file for signing")
    parser.add_argument("--cert", help="certificate PEM file")
    parser.add_argument("--output", "-o", help="output path (default: overwrite input)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="allow re-signing an already-signed container",
    )
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the sign subcommand."""
    from jxz.signing import sign_container

    path = Path(args.file)
    if not path.is_file():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1

    # Load signing materials (fail fast)
    private_key = load_private_key(args.key)
    certificate = None
    if args.cert:
        certificate = load_certificate(args.cert)

    data = path.read_bytes()

    try:
        result = sign_container(data, private_key, certificate, force=args.force)
    except JxzError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    output_path = Path(args.output) if args.output else path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(result)
    print(str(output_path))
    return 0
