import stat
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
from pyls.types import DirEntries, ExitStatus, FileEntry, FileStatus


def gobble_file(
    path: Path,
    opts,
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
        exit_status |= int(gobble_file(child, opts, entries))
    return DirEntries(path=dir_path, entries=entries), ExitStatus(exit_status)


def extract_dirs_from_files(
    cwd_entries: list[FileEntry],
    pending_dirs: list[Path],
    opts,
) -> None:
    if opts.directory:
        return

    files: list[FileEntry] = []

    for entry in cwd_entries:
        if entry.is_dir:
            pending_dirs.append(entry.path)
        else:
            files.append(entry)

    cwd_entries.clear()
    cwd_entries.extend(files)


def collect_entries_bfs(paths: list[Path], opts) -> list[DirEntries]:
    result: list[DirEntries] = []
    dir_queue: list[Path] = list(paths)

    while dir_queue:
        d = dir_queue.pop(0)
        dir_entries, status = scan_dir_children(d, opts, entries=[])
        result.append(dir_entries)

        if opts.recursive:
            for entry in dir_entries.entries:
                if entry.is_dir and entry.name not in {".", ".."}:
                    dir_queue.append(entry.path)

    return result


def move_dirs_to_pending(
    entries: list[FileEntry],
    pending_queue: list[Path],
    opts,
) -> None:
    if opts.directory:
        return

    files: list[FileEntry] = []

    for entry in entries:
        if entry.is_dir:
            # TODO: 重複排除
            pending_queue.append(entry.path)
        else:
            files.append(entry)

    entries.clear()
    entries.extend(files)


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
        for entry in display_entries:
            prefix = format_prefix(entry, opts)

            print(prefix + format_entry_name(entry, opts))
