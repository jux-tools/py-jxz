# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Verify subcommand: verify container integrity and signatures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from jxz.cli import load_certificate
from jxz.errors import JxzError
from jxz.reader import ContainerReader

if TYPE_CHECKING:
    import argparse


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the verify subcommand."""
    parser = subparsers.add_parser("verify", help="verify a .jxz container")
    parser.add_argument("file", help="path to .jxz file")
    parser.add_argument("--cert", help="PEM certificate for signature verification")
    parser.add_argument(
        "--quiet", action="store_true", help="suppress output on success"
    )
    parser.add_argument(
        "--json", dest="json_output", action="store_true", help="JSON output"
    )
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the verify subcommand."""
    path = Path(args.file)
    if not path.is_file():
        msg = f"file not found: {args.file}"
        if args.json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(f"Error: {msg}", file=sys.stderr)
        return 1

    try:
        data = path.read_bytes()
        reader = ContainerReader(data)
    except JxzError as exc:
        msg = str(exc)
        if args.json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(f"Error: {msg}", file=sys.stderr)
        return 1

    certificate = None
    if args.cert:
        certificate = load_certificate(args.cert)

    try:
        reader.verify(certificate=certificate)
    except JxzError as exc:
        msg = str(exc)
        if args.json_output:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(f"Error: {msg}", file=sys.stderr)
        return 1

    if args.json_output:
        print(json.dumps({"status": "ok", "message": "Verification passed"}))
    elif not args.quiet:
        print("OK")

    return 0
