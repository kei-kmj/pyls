import fnmatch
import grp
import pwd
import re
import stat
from collections.abc import Iterable
from datetime import datetime, timedelta
from pathlib import Path

import xattr

from pyls.types import (
    EscapeSeq,
    FileEntry,
    FileTypeChar,
    Format,
    IndicatorChar,
    LongFormatLine,
    PermChar,
    SizeUnit,
    XattrChar,
)


def calculate_total_blocks(entries: list[FileEntry]) -> int:
    return sum(e.file_status.blocks for e in entries)


def filetype_char(st_mode: int) -> str:
    if stat.S_ISDIR(st_mode):
        return FileTypeChar.DIR
    if stat.S_ISLNK(st_mode):
        return FileTypeChar.LINK
    return FileTypeChar.REGULAR


def permission_string(st_mode: int) -> str:
    permission = []
    for who in (
        stat.S_IRUSR,
        stat.S_IWUSR,
        stat.S_IXUSR,
        stat.S_IRGRP,
        stat.S_IWGRP,
        stat.S_IXGRP,
        stat.S_IROTH,
        stat.S_IWOTH,
        stat.S_IXOTH,
    ):
        if st_mode & who:
            if who in (stat.S_IWUSR, stat.S_IWGRP, stat.S_IWOTH):
                permission.append(PermChar.WRITE)
            elif who in (stat.S_IRUSR, stat.S_IRGRP, stat.S_IROTH):
                permission.append(PermChar.READ)
            else:
                permission.append(PermChar.EXEC)
        else:
            permission.append(PermChar.NONE)
    return "".join(permission)


def max_width(lines: list[LongFormatLine], key) -> int:
    widths = [len(str(key(line))) for line in lines]
    return max(widths)


def pad_value(value, width: int, right: bool = True) -> str:
    if right:
        return str(value).rjust(width)
    else:
        return str(value).ljust(width)


def format_prefix(entry: FileEntry, opts) -> str:
    prefix = ""
    if opts.inode:
        prefix += f"{entry.file_status.inode} "
    if opts.size:
        prefix += f"{entry.file_status.blocks:>3} "
    return prefix


def format_line_with_widths(line: LongFormatLine, widths: dict[str, int], opts, entry: FileEntry | None = None) -> str:
    prefix = format_prefix(entry, opts) if entry else ""
    parts = [line.mode, pad_value(line.nlink, widths["nlink"])]

    if not opts.no_owner:
        parts.append(pad_value(line.owner, widths["owner"], right=False) + " ")

    if not opts.no_group:
        parts.append(pad_value(line.group, widths["group"], right=False))

    extra_space = "  " if (opts.no_owner and opts.no_group) else " "
    parts.append(extra_space + pad_value(line.size, widths["size"]))
    parts.append(line.time)
    parts.append(line.name)

    return prefix + " ".join(parts)


def extended_attribute_char(path: Path) -> str:
    try:
        attrs = xattr.listxattr(str(path))
        return XattrChar.PRESENT if attrs else XattrChar.ABSENT
    except OSError:
        return XattrChar.ABSENT


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


def format_time(timestamp: float) -> str:
    file_datetime = datetime.fromtimestamp(timestamp)
    now = datetime.now()
    six_months_ago = now - timedelta(days=180)

    if file_datetime < six_months_ago or file_datetime > now:
        return file_datetime.strftime(Format.DAY_WITH_YEAR)
    else:
        return file_datetime.strftime(Format.DAY_WITH_TIME)


def human_readable_size(size: int) -> str:
    if size < SizeUnit.THRESHOLD:
        return f" {size}B"

    fsize = float(size)
    for unit in ["K", "M", "G", "T", "P"]:
        fsize /= SizeUnit.THRESHOLD
        if fsize < SizeUnit.THRESHOLD:
            return f"{fsize:.0f}{unit}" if fsize >= SizeUnit.INT_DISPLAY_MIN else f" {fsize:.1f}{unit}"
    return f" {fsize:.1f}P"


def format_long_line(entry: FileEntry, opts) -> LongFormatLine:
    status = entry.file_status

    if opts.human_readable:
        size = human_readable_size(status.size)
    else:
        size = str(status.size)

    time_value = opts.time
    if time_value == "atime" or time_value == "access":
        display_time = status.atime
    elif time_value == "ctime" or time_value == "status":
        display_time = status.ctime
    else:
        display_time = status.mtime

    return LongFormatLine(
        mode=mode_string(status.mode) + extended_attribute_char(entry.path),
        nlink=status.nlink,
        owner=user_name(status.uid, numeric=opts.numeric_uid_gid),
        group=group_name(status.gid, numeric=opts.numeric_uid_gid),
        size=size,
        time=format_time(display_time),
        name=format_entry_name(entry, opts),
    )


def mode_string(st_mode: int) -> str:
    return filetype_char(st_mode) + permission_string(st_mode)


def c_escape(s: str) -> str:
    output: list[str] = []

    for ch in s:
        if ch in EscapeSeq.MAP:
            output.append(EscapeSeq.MAP[ch])
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


def natural_sort_key(name: str) -> list:
    parts = re.split(r"(\d+)", name.lower())
    return [int(p) if p.isdigit() else p for p in parts]


def iter_display_entries(entries: list[FileEntry], opts) -> list[FileEntry]:
    if opts.unsorted or opts.sort == "none":
        return list(entries)

    if opts.sort_time or opts.sort == "time":
        return sorted(entries, key=lambda e: e.file_status.mtime, reverse=not opts.reverse)

    if opts.sort_size or opts.sort == "size":
        return sorted(entries, key=lambda e: e.file_status.size, reverse=not opts.reverse)

    if opts.sort_extension or opts.sort == "extension":

        def ext_key(e: FileEntry) -> tuple[str, str]:
            name = e.name
            if "." in name:
                extension = name.rsplit(".", 1)[1].lower()
            else:
                extension = ""
            return extension, name.lower()

        return sorted(entries, key=ext_key, reverse=opts.reverse)

    if opts.sort_version or opts.sort == "version":
        return sorted(entries, key=lambda e: natural_sort_key(e.name), reverse=opts.reverse)

    return sorted(entries, key=lambda e: e.name.lower(), reverse=opts.reverse)


def quote_double(s: str) -> str:
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def should_ignore(name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def filter_ignored(entries: Iterable[FileEntry], opts) -> list[FileEntry]:
    patterns = list(opts.ignore)

    if not (opts.all or opts.almost_all):
        if opts.hide:
            patterns.append(opts.hide)

    if not patterns:
        return list(entries)
    return [e for e in entries if not should_ignore(e.name, patterns)]


def file_type_indicator(entry: FileEntry, opts) -> str:
    if opts.classify or opts.p or opts.file_type:
        if entry.is_dir:
            return IndicatorChar.DIR

    if opts.classify or opts.p or opts.file_type:
        mode = entry.file_status.mode

        if entry.is_dir:
            return IndicatorChar.DIR
        if stat.S_ISLNK(mode):
            return IndicatorChar.LINK
        if stat.S_ISFIFO(mode):
            return IndicatorChar.FIFO
        if stat.S_ISSOCK(mode):
            return IndicatorChar.SOCKET

        exec_any = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        if opts.classify and (mode & exec_any):
            return IndicatorChar.EXEC

    return ""


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

    name += file_type_indicator(entry, opts)

    return name
