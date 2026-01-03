from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pyls.cli import build_parser
from pyls.core import FileEntry, collect_entries, gobble_file, scan_dir_children, classify_paths
from pyls.output import print_newline_except_last, print_files, print_directory, print_subdirs_recursively


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    args = build_parser().parse_args(argv)
    args.colorize = sys.stdout.isatty()
    paths = args.paths if args.paths else ["."]
    files, dirs = classify_paths(paths, args)

    if args.recursive:
        show_header = True
    else:
        show_header = len(dirs) >= 1 and len(paths) > 1

    if files:
        print_files(files, args)

    all_subdirs: list[Path] = []
    for d in dirs:
        subdirs = print_directory(d, args, show_header)
        all_subdirs.extend(subdirs)

    if args.recursive:
        print_subdirs_recursively(all_subdirs, args)
