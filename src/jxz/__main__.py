# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""python -m jxz CLI dispatcher."""

from __future__ import annotations

import argparse
import sys

from jxz import __version__
from jxz.cli import build, extract, inspect, sign, verify


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="jxz",
        description="Build, inspect, sign, verify, and extract .jxz signed containers.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command")
    build.register(subparsers)
    inspect.register(subparsers)
    sign.register(subparsers)
    verify.register(subparsers)
    extract.register(subparsers)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)  # type: ignore[no-any-return]


if __name__ == "__main__":
    sys.exit(main())
