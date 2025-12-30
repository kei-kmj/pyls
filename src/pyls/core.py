import stat
from pathlib import Path

from pyls.display import iter_display_entries, format_entry_name
from pyls.types import FileEntry, ExitStatus, ScanPathsResult


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

    is_dir = stat.S_ISDIR(st.st_mode)
    name = path.name or str(path)
    entry = FileEntry(path=path, name=name, is_dir=is_dir )
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
        entries.append(FileEntry(path=dir_path, name=".", is_dir=True))
        entries.append(FileEntry(path=dir_path.parent, name="..", is_dir=True))

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



def print_names(entries: list[FileEntry], opts) -> None:
    for entry in iter_display_entries(entries, opts):
        print(format_entry_name(entry, opts))