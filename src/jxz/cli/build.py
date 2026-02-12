# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Build subcommand: assemble .jxz containers from JUnit XML reports."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from jxz.builder import ContainerBuilder
from jxz.cli import load_certificate, load_private_key

if TYPE_CHECKING:
    import argparse


def _parse_attachment(spec: str) -> tuple[Path, str | None]:
    """Parse an attachment spec into (path, test_id | None).

    Format: ``PATH`` or ``PATH:TEST_ID``.
    Uses rfind(":") to split, but checks that the right side does not
    contain path separators (to handle colons in Windows paths or URIs).
    """
    idx = spec.rfind(":")
    if idx > 0:
        right = spec[idx + 1 :]
        if "/" not in right and "\\" not in right and right:
            return Path(spec[:idx]), right
    return Path(spec), None


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the build subcommand."""
    parser = subparsers.add_parser("build", help="build a .jxz container")
    parser.add_argument("report", help="path to JUnit XML report file")
    parser.add_argument(
        "--created-by", required=True, help="tool identifier (e.g. pytest-jux/0.1.0)"
    )
    parser.add_argument(
        "--report-type", required=True, help="report dialect (e.g. pytest-junit)"
    )
    parser.add_argument(
        "--attachment",
        action="append",
        default=[],
        metavar="PATH[:TEST_ID]",
        help="attachment file (repeatable)",
    )
    parser.add_argument(
        "--meta",
        action="append",
        default=[],
        metavar="FILE",
        help="file to add under META-INF/ (repeatable)",
    )
    parser.add_argument("--key", help="private key PEM file for signing")
    parser.add_argument("--cert", help="certificate PEM file (requires --key)")
    parser.add_argument("--output", "-o", help="output path (default: <report>.jxz)")
    parser.add_argument("--timestamp", help="ISO 8601 timestamp (default: now UTC)")
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the build subcommand."""
    # Validate report file
    report_path = Path(args.report)
    if not report_path.is_file():
        print(f"Error: report file not found: {args.report}", file=sys.stderr)
        return 1

    # Validate --cert requires --key
    if args.cert and not args.key:
        print("Error: --cert requires --key", file=sys.stderr)
        return 1

    # Parse timestamp
    timestamp: datetime | None = None
    if args.timestamp:
        try:
            timestamp = datetime.fromisoformat(args.timestamp)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=UTC)
        except ValueError:
            print(f"Error: invalid timestamp: {args.timestamp}", file=sys.stderr)
            return 1

    # Load signing materials (before reading files, to fail fast)
    private_key = None
    certificate = None
    if args.key:
        private_key = load_private_key(args.key)
    if args.cert:
        certificate = load_certificate(args.cert)

    # Read report
    report_data = report_path.read_bytes()

    # Build container
    builder = ContainerBuilder()
    builder.set_report(report_data)

    # Add attachments
    for spec in args.attachment:
        att_path, test_id = _parse_attachment(spec)
        if not att_path.is_file():
            print(f"Error: attachment file not found: {att_path}", file=sys.stderr)
            return 1
        builder.add_attachment(
            att_path.name, att_path.read_bytes(), attachment_for=test_id
        )

    # Add meta files
    for meta_spec in args.meta:
        meta_path = Path(meta_spec)
        if not meta_path.is_file():
            print(f"Error: meta file not found: {meta_path}", file=sys.stderr)
            return 1
        builder.add_meta(meta_path.name, meta_path.read_bytes())

    # Build
    jxz_bytes = builder.build(
        created_by=args.created_by,
        report_type=args.report_type,
        timestamp=timestamp,
        private_key=private_key,
        certificate=certificate,
    )

    # Determine output path
    output_path = Path(args.output) if args.output else report_path.with_suffix(".jxz")

    # Create parent directories if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_bytes(jxz_bytes)
    print(str(output_path))
    return 0
