# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Inspect subcommand: display container metadata and contents."""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

from jxz.cli import format_size
from jxz.errors import JxzError
from jxz.manifest import compute_digest
from jxz.reader import ContainerReader

_DS_NS = "http://www.w3.org/2000/09/xmldsig#"

if TYPE_CHECKING:
    import argparse


class _FileInfo(TypedDict):
    name: str
    size: int
    sha256: str


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the inspect subcommand."""
    parser = subparsers.add_parser("inspect", help="inspect a .jxz container")
    parser.add_argument("file", help="path to .jxz file")
    parser.add_argument(
        "--json", dest="json_output", action="store_true", help="JSON output"
    )
    parser.set_defaults(func=run)


def _signature_info(reader: ContainerReader) -> str:
    """Return human-readable signature info."""
    if not reader.is_signed:
        return "No"
    sig = reader.get_signature_xml()
    if sig is not None:
        try:
            root = ET.fromstring(sig)
            method = root.find(f".//{{{_DS_NS}}}SignatureMethod")
            if method is not None:
                algo = (method.get("Algorithm") or "").lower()
                if "rsa-sha256" in algo:
                    return "Yes (RSA-SHA256)"
                if "ecdsa-sha256" in algo:
                    return "Yes (ECDSA-SHA256)"
        except ET.ParseError:
            pass
    return "Yes"


def run(args: argparse.Namespace) -> int:
    """Execute the inspect subcommand."""
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

    manifest = reader.get_manifest()

    # Collect file info
    files: list[_FileInfo] = []
    for entry in manifest.entries:
        name = entry["Name"]
        size = int(entry["Size"])
        digest = entry["SHA-256"]
        files.append({"name": name, "size": size, "sha256": digest})

    # Also include META-INF extras not in manifest entries
    meta = reader.get_meta()
    meta_names_in_entries = {e["Name"] for e in manifest.entries}
    for meta_name, meta_data in meta.items():
        full_name = f"META-INF/{meta_name}"
        if full_name not in meta_names_in_entries:
            files.append(
                {
                    "name": full_name,
                    "size": len(meta_data),
                    "sha256": compute_digest(meta_data),
                }
            )

    if args.json_output:
        output = {
            "file": str(path),
            "created_by": reader.created_by,
            "report_type": reader.report_type,
            "timestamp": manifest.main["Timestamp"],
            "signed": reader.is_signed,
            "signature": _signature_info(reader) if reader.is_signed else None,
            "files": files,
        }
        print(json.dumps(output, indent=2))
        return 0

    # Human-readable output
    print(f"Container: {path.name}")
    print(f"  Created-By:  {reader.created_by}")
    print(f"  Report-Type: {reader.report_type}")
    print(f"  Timestamp:   {manifest.main['Timestamp']}")
    print(f"  Signed:      {_signature_info(reader)}")
    print()
    print(f"Files ({len(files)}):")
    print(f"  {'Name':<40s} {'Size':>8s}   SHA-256")
    for f in files:
        print(f"  {f['name']:<40s} {format_size(f['size']):>8s}   {f['sha256'][:8]}...")

    return 0
