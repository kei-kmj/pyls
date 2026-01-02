import stat
import sys
from pathlib import Path

from pyls.filter import iter_display_entries
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
