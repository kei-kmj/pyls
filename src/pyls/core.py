import stat
from pathlib import Path

from pyls.display import filter_ignored, format_entry_name, iter_display_entries, format_long_line, \
    calculate_total_blocks, max_width, format_line_with_widths
from pyls.types import ExitStatus, FileEntry, ScanPathsResult, FileStatus


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
) -> ExitStatus:
    try:
        children = list(dir_path.iterdir())
    except FileNotFoundError:
        print(f"pyls: cannot access '{dir_path}': No such file or directory")
        return ExitStatus.ERROR
    except PermissionError:
        print(f"pyls: cannot access '{dir_path}': Permission denied")
        return ExitStatus.ERROR

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
    return ExitStatus(exit_status)



def extract_dirs_from_files(
        cwd_entries: list[FileEntry],
        pending_dirs: list[Path],
        opts,
) -> None:
    if opts.directory:
        return

    files:list[FileEntry] = []

    for entry in cwd_entries:
        if entry.is_dir:
            pending_dirs.append(entry.path)
        else:
            files.append(entry)

    cwd_entries.clear()
    cwd_entries.extend(files)


def collect_entries_bfs(paths: list[Path],opts)-> ScanPathsResult:
    entries: list[FileEntry] = []
    dir_queue: list[Path] = []
    exit_status = ExitStatus.OK

    for p in paths:
        exit_status |= gobble_file(p, opts, entries)

    move_dirs_to_pending(entries, dir_queue, opts)

    if not opts.recursive:
        for d in list(dir_queue):
            exit_status |= scan_dir_children(d, opts, entries)
        return ScanPathsResult(entries=entries, dir_queue=dir_queue, exit_status=ExitStatus(exit_status))

    i = 0
    while i < len(dir_queue):
        d = dir_queue[i]
        i += 1
        exit_status |= scan_dir_children(d, opts, entries)
        move_dirs_to_pending(entries, dir_queue, opts)
    return ScanPathsResult(entries, dir_queue, ExitStatus(exit_status))


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

    if opts.long:
        print(f"total {calculate_total_blocks(display_entries)}")

        # 1パス目：生データ収集
        raw_lines = [format_long_line(entry, opts) for entry in display_entries]

        # 幅計算
        widths = {
            'nlink': max_width(raw_lines, lambda l: l.nlink),
            'owner': max_width(raw_lines, lambda l: l.owner),
            'group': max_width(raw_lines, lambda l: l.group),
            'size': max_width(raw_lines, lambda l: l.size),
        }

        # 2パス目：整形して出力
        for line in raw_lines:
            print(format_line_with_widths(line, widths))
    else:
        for entry in display_entries:
            print(format_entry_name(entry, opts))

