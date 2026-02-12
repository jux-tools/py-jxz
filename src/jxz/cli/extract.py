# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Extract subcommand: extract container contents to disk."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from jxz.errors import JxzError
from jxz.reader import ContainerReader

if TYPE_CHECKING:
    import argparse


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the extract subcommand."""
    parser = subparsers.add_parser("extract", help="extract .jxz container contents")
    parser.add_argument("file", help="path to .jxz file")
    parser.add_argument(
        "--output", "-o", default=".", help="output directory (default: .)"
    )
    parser.add_argument(
        "--report-only", action="store_true", help="extract only junit.xml"
    )
    parser.add_argument(
        "--attachments-only", action="store_true", help="extract only attachments/"
    )
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the extract subcommand."""
    path = Path(args.file)
    if not path.is_file():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1

    try:
        data = path.read_bytes()
        reader = ContainerReader(data)
    except JxzError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # Validate digests before extracting
    try:
        reader.validate()
    except JxzError as exc:
        print(f"Error: container integrity check failed: {exc}", file=sys.stderr)
        return 1

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    extracted: list[str] = []

    if not args.attachments_only:
        # Extract report
        report_path = output_dir / "junit.xml"
        report_path.write_bytes(reader.get_report())
        extracted.append(str(report_path))

    if not args.report_only:
        # Extract attachments
        for rel_name, content in reader.get_attachments().items():
            att_path = output_dir / "attachments" / rel_name
            att_path.parent.mkdir(parents=True, exist_ok=True)
            att_path.write_bytes(content)
            extracted.append(str(att_path))

    if not args.report_only and not args.attachments_only:
        # Extract META-INF extras
        for meta_name, content in reader.get_meta().items():
            meta_path = output_dir / "META-INF" / meta_name
            meta_path.parent.mkdir(parents=True, exist_ok=True)
            meta_path.write_bytes(content)
            extracted.append(str(meta_path))

    for p in extracted:
        print(p)

    return 0
