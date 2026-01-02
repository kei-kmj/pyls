import stat
import sys
from pathlib import Path

from pyls.display import (
    calculate_total_blocks,
    filter_ignored,
    format_entry_name,
    format_line_with_widths,
    format_long_line,
    format_prefix,
    iter_display_entries,
    max_width,
)
from pyls.layout import get_terminal_width, print_columns, print_newline_except_last
from pyls.types import DirectoryIdentifier, DirEntries, ExitStatus, FileEntry, FileStatus


def gobble_file(
    path: Path,
    cwd_entries: list[FileEntry],
) -> ExitStatus:
    try:
        st = path.lstat()

    except FileNotFoundError:
        print(f"pyls: cannot access '{path}': No such file or directory")
        return ExitStatus.ERROR
    except PermissionError:
        print(f"pyls: cannot access '{path}': Permission denied")
        return ExitStatus.ERROR

    file_status = FileStatus.from_stat_result(st)

    is_dir = stat.S_ISDIR(st.st_mode)
    name = path.name or str(path)
    entry = FileEntry(path=path, name=name, is_dir=is_dir, file_status=file_status)
    cwd_entries.append(entry)
    return ExitStatus.OK


def should_include(name: str, opts) -> bool:
    if opts.all:
        return True

    if opts.almost_all:
        return name not in {".", ".."}

    return not name.startswith(".")


def scan_dir_children(
    dir_path: Path,
    opts,
    entries: list[FileEntry],
) -> tuple[DirEntries, ExitStatus]:
    try:
        children = list(dir_path.iterdir())
    except FileNotFoundError:
        print(f"pyls: cannot access '{dir_path}': No such file or directory")
        return DirEntries(path=dir_path, entries=[]), ExitStatus.ERROR
    except PermissionError:
        print(f"pyls: cannot access '{dir_path}': Permission denied")
        return DirEntries(path=dir_path, entries=[]), ExitStatus.ERROR

    if opts.all:
        dot_status = FileStatus.from_stat_result(dir_path.lstat())
        dotdot_status = FileStatus.from_stat_result(dir_path.parent.lstat())
        entries.append(FileEntry(path=dir_path, name=".", is_dir=True, file_status=dot_status))
        entries.append(FileEntry(path=dir_path.parent, name="..", is_dir=True, file_status=dotdot_status))

    exit_status = ExitStatus.OK
    for child in children:
        if not should_include(child.name, opts):
            continue
        exit_status |= int(gobble_file(child, entries))

    sorted_entries = iter_display_entries(entries, opts)
    return DirEntries(path=dir_path, entries=sorted_entries), ExitStatus(exit_status)


def collect_entries(paths: list[Path], opts) -> list[DirEntries]:
    result: list[DirEntries] = []
    pending_dirs: list[Path] = list(paths)
    visited_dirs: set[DirectoryIdentifier] = set()

    while pending_dirs:
        d = pending_dirs.pop(0)

        try:
            stat_info = d.stat()
            dir_id = DirectoryIdentifier(stat_info.st_dev, stat_info.st_ino)
            if dir_id in visited_dirs:
                print(f"pyls: {d}: not listing already-listed directory", file=sys.stderr)
                continue
            visited_dirs.add(dir_id)
        except OSError:
            pass

        dir_entries, status = scan_dir_children(d, opts, entries=[])
        result.append(dir_entries)

        if opts.recursive:
            subdirs = [entry.path for entry in dir_entries.entries if entry.is_dir and entry.name not in {".", ".."}]
            pending_dirs = subdirs + pending_dirs  # DFS

    return result


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
            terminal_width = opts.width if opts.width else get_terminal_width()
            tab_size = opts.tabsize if opts.tabsize else 8
            print_columns(names, terminal_width, tab_size)
            print()
