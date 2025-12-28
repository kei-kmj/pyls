from __future__ import annotations

import argparse
import sys

from pyls.cli import build_parser


def print_args(args: argparse.Namespace) -> None:
    fields = [
        "all",
        "almost_all",
        "escape",
        "directory",
        "file_type",
        "classify",
        "no_owner",
        "human_readable",
        "hide",
        "inode",
        "ignore",
        "long",
        "numeric_uid_gid",
        "literal",
        "no_group",
        "p",
        "indicator_style",
        "hide_control_chars",
        "quote_name",
        "reverse",
        "recursive",
        "size",
        "sort",
        "sort_size",
        "sort_time",
        "time",
        "tabsize",
        "no_sort",
        "sort_version",
        "sort_extension",
        "width",
        "context",
        "one_column",
        "paths",
    ]
    for f in fields:
        if not hasattr(args, f):
            continue
        value = getattr(args, f)

        # フラグ系: True のときだけ表示
        if value is True:
            print(f"received {f}")
        # 値を取る系: None じゃなければ表示（文字列/数値）
        elif value not in (None, False):
            print(f"received {f}={value!r}")


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    args = build_parser().parse_args(argv)

    print_args(args)

    for p in args.paths:
        print(p)