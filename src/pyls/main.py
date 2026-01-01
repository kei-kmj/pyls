from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pyls.cli import build_parser
from pyls.core import FileEntry, collect_entries_bfs, gobble_file, print_entries, scan_dir_children


def print_args(args: argparse.Namespace) -> None:
    fields = [  # noqa: F841
        "hide",
        "inode",
        "sort",
        "sort_size",
        "sort_time",
        "time",
        "tabsize",
        "sort_version",
        "sort_extension",
        "width",
    ]


def classify_paths(
    paths: list[str],
) -> tuple[list[Path], list[Path]]:
    files: list[Path] = []
    dirs: list[Path] = []

    for p in paths:
        path = Path(p)
        if path.is_dir():
            dirs.append(path)
        else:
            files.append(path)

    return files, dirs


def print_files(files: list[Path], args: argparse.Namespace) -> None:
    entries: list[FileEntry] = []

    for f in files:
        gobble_file(f, args, entries)
    print_entries(entries, args)


def print_directory(d: Path, args, show_header: bool) -> list[Path]:
    if show_header:
        print(f"{d}:")

    dir_entries, _ = scan_dir_children(d, args, entries=[])
    print_entries(dir_entries.entries, args)

    return [entry.path for entry in dir_entries.entries if entry.is_dir and entry.name not in {".", ".."}]


def print_subdirs_recursively(subdirs: list[Path], args) -> None:
    for sub_entry in collect_entries_bfs(subdirs, args):
        print(f"{sub_entry.path}:")
        print_entries(sub_entry.entries, args)
        print()


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    args = build_parser().parse_args(argv)
    paths = args.paths if args.paths else ["."]
    files, dirs = classify_paths(paths)

    show_header = len(dirs) >= 1 and len(paths) > 1

    if files:
        print_files(files, args)
        print()

    all_subdirs: list[Path] = []
    for d in dirs:
        subdirs = print_directory(d, args, show_header)
        all_subdirs.extend(subdirs)
        print()

    if args.recursive:
        print_subdirs_recursively(all_subdirs, args)
