import fnmatch
import grp
import pwd
import stat
import xattr
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from pyls.types import FileEntry, LongFormatLine


def filetype_char(st_mode: int) -> str:
    if stat.S_ISDIR(st_mode):
        return "d"
    if stat.S_ISLNK(st_mode):
        return "l"
    return "-"

def permission_string(st_mode: int) -> str:
    permission = []
    for who in (stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR,
                stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP,
                stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH):
        if st_mode & who:
            if who in (stat.S_IWUSR, stat.S_IWGRP, stat.S_IWOTH):
                permission.append("w")
            elif who in (stat.S_IRUSR, stat.S_IRGRP, stat.S_IROTH):
                permission.append("r")
            else:
                permission.append("x")
        else:
            permission.append("-")
    return "".join(permission)


def extended_attribute_char(path: Path) -> str:
    try:
        attrs = xattr.listxattr(str(path))
        return "@" if attrs else " "
    except (OSError, IOError):
        return " "


def user_name(uid: int, numeric: bool) -> str:
    if numeric:
        return str(uid)
    try:
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return str(uid)

def group_name(gid: int, numeric: bool) -> str:
    if numeric:
        return str(gid)
    try:
        return grp.getgrgid(gid).gr_name
    except KeyError:
        return str(gid)


def format_mtime(epoch: float) -> str:
    dt = datetime.fromtimestamp(epoch)
    return dt.strftime("%b %d %H:%M")


def format_long_line(entry: FileEntry, opts) -> LongFormatLine:
    status = entry.file_status

    return LongFormatLine(
        mode=mode_string(status.mode) + extended_attribute_char(entry.path),
        nlink=status.nlink,
        owner=user_name(status.uid, numeric=getattr(opts, "numeric_uid_gid", False)),
        group=group_name(status.gid, numeric=getattr(opts, "numeric_uid_gid", False)),
        size=status.size,
        mtime=format_mtime(status.mtime),
        name=format_entry_name(entry, opts),
    )


def mode_string(st_mode: int) -> str:
    return filetype_char(st_mode) + permission_string(st_mode)



def c_escape(s: str) -> str:
    output: list[str] = []

    for ch in s:
        if ch == "\n":
            output.append("\\n")
            continue
        if ch == "\t":
            output.append("\\t")
            continue
        if ch == "\r":
            output.append("\\r")
            continue

        if ch == "\\":
            output.append("\\\\")
            continue

        if ch.isprintable():
            output.append(ch)
            continue

        code = ord(ch)
        if code <= 0xFF:
            output.append(f"\\x{code:02x}")
        elif code <= 0xFFFF:
            output.append(f"\\u{code:04x}")
        else:
            output.append(f"\\U{code:08x}")

    return "".join(output)



def replace_nonprintable(s: str) -> str:
    return "".join(ch if ch.isprintable() else "?" for ch in s)


def iter_display_entries(entries: list[FileEntry], opts) -> list[FileEntry]:
    if opts.unsorted:
        return list(entries)
    return sorted(entries, key=lambda e: e.name, reverse=opts.reverse)


def quote_double(s: str) -> str:
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def should_ignore(name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def filter_ignored(entries: Iterable[FileEntry], opts) -> list[FileEntry]:
    patterns: list[str] = getattr(opts, "ignore", [])
    if not patterns:
        return list(entries)
    return [e for e in entries if not should_ignore(e.name, patterns)]


def format_entry_name(entry: FileEntry, opts) -> str:

    if opts.literal:
        return entry.name

    name = entry.name

    if opts.escape:
        name = c_escape(name)

    if opts.hide_control_chars:
        name = replace_nonprintable(name)

    if opts.quote_name:
        name = quote_double(name)

    if opts.indicator_style and entry.is_dir:
        name += "/"

    return name
