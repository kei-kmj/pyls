import grp
import pwd
import shlex
import stat
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
        prefix += f"{entry.file_status.blocks} "
    return prefix


def format_line_with_widths(line: LongFormatLine, widths: dict[str, int], opts, entry: FileEntry | None = None) -> str:
    prefix = format_prefix(entry, opts) if entry else ""
    parts = [line.mode, pad_value(line.nlink, widths["nlink"])]

    if not opts.no_owner:
        parts.append(pad_value(line.owner, widths["owner"], right=False))

    if not opts.no_group:
        parts.append(pad_value(line.group, widths["group"], right=False))

    parts.append(pad_value(line.size, widths["size"]))
    parts.append(line.time)
    parts.append(line.name)

    return prefix + " ".join(parts)


def extended_attribute_char(path: Path) -> str:
    try:
        attrs = xattr.listxattr(str(path))
        return XattrChar.PRESENT if attrs else ""
    except OSError:
        return ""


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


def quote_double(s: str) -> str:
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


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


BLUE = "\033[1;34m"
RESET = "\033[0m"


def shell_quote_ansi_c(s: str) -> str:
    """Shell-safe quoting with ANSI-C style for special chars"""
    # 特殊文字があるかチェック
    needs_quoting = any(c in ' \t\n\r\'"\\' or not c.isprintable() for c in s)
    if not needs_quoting:
        return s

    has_single = "'" in s
    has_double = '"' in s
    has_nonprintable = any(not c.isprintable() for c in s)

    # シングルクォートがあり、ダブルクォートがなく、非表示文字もない
    if has_single and not has_double and not has_nonprintable:
        return f'"{s}"'


        # ANSI-C quoting
    result = '"' if has_single else "'"
    for c in s:
        if c == '\\':
            result += '\\\\'
        elif c == '\t':
            result += "'$'"'\\t'"\'""\'"
        elif c == '\n':
            result += "'$'"'\\n'"\'""\'"
        elif c == '\r':
            result += '\\r'
        elif c == "'":
            result += "\\'"
        else:
            result += c
    result += '"' if has_single else "'"
    return result


def format_entry_name(entry: FileEntry, opts) -> str:
    name = entry.name

    if not (opts.literal or opts.escape or opts.quote_name or opts.p):
        name = shell_quote_ansi_c(name)
        name += file_type_indicator(entry, opts)
        return name

    if opts.literal:
        name = replace_nonprintable(name)
        name += file_type_indicator(entry, opts)
        return name

    if opts.escape:
        name = c_escape(name)

    if opts.hide_control_chars:
        name = replace_nonprintable(name)

    if opts.quote_name:
        name = quote_double(name)

    if entry.is_dir and opts.colorize:
        name = f"{BLUE}{name}{RESET}"

    name += file_type_indicator(entry, opts)

    return name
