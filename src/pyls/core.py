import stat
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path


class ExitStatus(IntEnum):
    OK = 0
    ERROR = 1



@dataclass(frozen=True)
class FileEntry:
    path: Path
    name: str
    is_dir: bool


@dataclass(frozen=True)
class ScanPathsResult:
    entries: list[FileEntry]
    pending_dirs: list[Path]
    exit_status: ExitStatus


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

    exit_status = ExitStatus.OK
    for child in children:
        exit_status |= gobble_file(child, opts, entries)
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