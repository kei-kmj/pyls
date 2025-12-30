from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pyls.cli import build_parser
from pyls.core import FileEntry, collect_entries_bfs, gobble_file, print_names


def print_args(args: argparse.Namespace) -> None:
    fields = [
        "file_type",
        "classify",
        "no_owner",
        "human_readable",
        "hide",
        "inode",
        "long",
        "numeric_uid_gid",
        "no_group",
        "recursive",
        "size",
        "sort",
        "sort_size",
        "sort_time",
        "time",
        "tabsize",
        "sort_version",
        "sort_extension",
        "width",
        "context"
    ]
    for f in fields:
        if not hasattr(args, f):
            continue
        value = getattr(args, f)

        # フラグ系: True のときだけ表示
        # if value is True:
        #     print(f"received {f}")
        # # 値を取る系: None じゃなければ表示（文字列/数値）
        # elif value not in (None, False):
        #     print(f"received {f}={value!r}")


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    args = build_parser().parse_args(argv)

    cwd_entries: list[FileEntry] = []

    status = 0
    paths = [Path(p) for p in (args.paths if args.paths else ["."])]
    for p in paths:
        status = max(status, gobble_file(Path(p), args, cwd_entries))

    print_args(args)
    # for p in args.paths:
    #     print(p)

    result = collect_entries_bfs(paths, args)
    print_names(result.entries, args)
