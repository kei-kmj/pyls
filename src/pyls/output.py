import argparse
import shutil
from pathlib import Path

from pyls.core import collect_entries, gobble_file, scan_dir_children
from pyls.filter import filter_ignored, iter_display_entries
from pyls.format import (
    calculate_total_blocks,
    format_entry_name,
    format_line_with_widths,
    format_long_line,
    format_prefix,
    human_readable_size,
    max_width,
)
from pyls.types import FileEntry


def print_entries(entries: list[FileEntry], opts) -> None:
    filtered_entries = filter_ignored(entries, opts)
    display_entries = list(iter_display_entries(filtered_entries, opts))

    if opts.numeric_uid_gid or opts.no_owner:
        opts.long = True

    if opts.long or opts.size:
        total_blocks = calculate_total_blocks(display_entries)
        if opts.human_readable:
            total_str = human_readable_size(total_blocks * 512)
        else:
            total_str = str(total_blocks)
        print(f"total {total_str}")

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
                print(name)
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

    # 最大可能カラム数 (MIN_COLUMN_WIDTH = 3: 1文字 + 2スペース)
    max_cols = min(len(names), max(1, terminal_width // 3))

    # 各カラム数配置の情報を初期化
    col_widths = {cols: [0] * cols for cols in range(1, max_cols + 1)}
    valid = {cols: True for cols in range(1, max_cols + 1)}

    # 各ファイルを処理して、無効なカラム数を除外
    for i, name in enumerate(names):
        name_len = len(name)
        for cols in range(1, max_cols + 1):
            if not valid[cols]:
                continue
            rows = (len(names) + cols - 1) // cols
            col = i // rows
            col_widths[cols][col] = max(col_widths[cols][col], name_len + 2)
            if sum(col_widths[cols]) - 2 > terminal_width:
                valid[cols] = False

    # 有効な最大カラム数を見つける
    cols = max(c for c in range(1, max_cols + 1) if valid[c])
    rows = (len(names) + cols - 1) // cols
    widths = col_widths[cols]

    # 表示
    for row in range(rows):
        for col in range(cols):
            idx = col * rows + row
            if idx < len(names):
                if col < cols - 1:
                    print(names[idx].ljust(widths[col]), end="")
                else:
                    print(names[idx], end="")
        print_newline_except_last(row, rows)
