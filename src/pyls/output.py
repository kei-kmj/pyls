import argparse
import shutil

from pathlib import Path

from pyls.core import gobble_file, scan_dir_children, collect_entries
from pyls.filter import filter_ignored, iter_display_entries
from pyls.format import calculate_total_blocks, format_long_line, max_width, format_line_with_widths, format_prefix, \
    format_entry_name
from pyls.types import (
    FileEntry
)

def print_entries(entries: list[FileEntry], opts) -> None:
    filtered_entries = filter_ignored(entries, opts)
    display_entries = list(iter_display_entries(filtered_entries, opts))

    if opts.long or opts.size:
        print(f"total {calculate_total_blocks(display_entries)}")

    if opts.long:
        # 1パス目：生データ収集
        raw_lines = [format_long_line(entry, opts) for entry in display_entries]

        # 幅計算
        widths = {
            "nlink": max_width(raw_lines, lambda x: x.nlink),
            "owner": max_width(raw_lines, lambda x: x.owner),
            "group": max_width(raw_lines, lambda x: x.group),
            "size": max_width(raw_lines, lambda x: x.size),
        }

        # 2パス目：整形して出力
        for entry, line in zip(display_entries, raw_lines):
            print(format_line_with_widths(line, widths, opts, entry))
    else:
        names = []
        for entry in display_entries:
            prefix = format_prefix(entry, opts)
            names.append(prefix + format_entry_name(entry, opts))

        if opts.one_column:
            for i, name in enumerate(names):
                print(name, end="")
                print_newline_except_last(i, len(names))
        else:
            terminal_width = opts.width if opts.width else current_terminal_width()
            tab_size = opts.tabsize if opts.tabsize else 8
            print_columns(names, terminal_width, tab_size)
            print()


def print_files(files: list[Path], args: argparse.Namespace) -> None:
    entries: list[FileEntry] = []

    for f in files:
        gobble_file(f, entries)
    print_entries(entries, args)


def print_directory(d: Path, args, show_header: bool) -> list[Path]:
    if show_header:
        print(f"{d}:")

    dir_entries, _ = scan_dir_children(d, args, entries=[])
    print_entries(dir_entries.entries, args)

    return [entry.path for entry in dir_entries.entries if entry.is_dir and entry.name not in {".", ".."}]


def print_subdirs_recursively(subdirs: list[Path], args) -> None:
    entries_list = list(collect_entries(subdirs, args))
    start_with_dot = not args.paths or args.paths == ["."]

    for i, sub_entry in enumerate(entries_list):
        path_str = str(sub_entry.path)
        if start_with_dot:
            path_str = "./" + path_str
        print(f"{path_str}:")
        print_entries(sub_entry.entries, args)
        print_newline_except_last(i, len(entries_list))



def print_newline_except_last(index: int, total: int) -> None:
    print("\n" if index + 1 < total else "", end="")


def current_terminal_width() -> int:
    return shutil.get_terminal_size().columns


def print_columns(names: list[str], terminal_width: int, tab_size: int = 8) -> None:
    """ファイル名を横並びで表示"""
    if not names:
        return

    max_len = max(len(name) for name in names)
    col_width = ((max_len // tab_size) + 1) * tab_size

    # 収まる最大の列数を計算
    columns = max(1, terminal_width // col_width)

    # 行数を計算
    rows = (len(names) + columns - 1) // columns

    # 縦方向に表示
    for row in range(rows):
        for col in range(columns):
            idx = col * rows + row
            if idx < len(names):
                print(names[idx].ljust(col_width), end="")
        print_newline_except_last(row, rows)
