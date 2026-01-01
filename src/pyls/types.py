import os
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path


class ExitStatus(IntEnum):
    OK = 0
    ERROR = 1


class FileTypeChar:
    DIR = "d"
    LINK = "l"
    REGULAR = "-"


class PermChar:
    READ = "r"
    WRITE = "w"
    EXEC = "x"
    NONE = "-"


class XattrChar:
    PRESENT = "@"
    ABSENT = " "


class SizeUnit:
    THRESHOLD = 1024
    UNITS = ("B", "K", "M", "G", "T", "P")
    INT_DISPLAY_MIN = 10


class IndicatorChar:
    DIR = "/"
    EXEC = "*"
    LINK = "@"
    FIFO = "|"
    SOCKET = "="


class EscapeSeq:
    MAP = {
        "\n": "\\n",
        "\t": "\\t",
        "\r": "\\r",
        "\\": "\\\\",
    }


class Format:
    DAY_WITH_TIME = "%b %d %H:%M"
    DAY_WITH_YEAR = "%b %d  %Y"
    QUOTE = '"'
    DIR_INDICATOR = "/"
    NONPRINTABLE = "?"


@dataclass(frozen=True)
class FileStatus:
    mode: int
    nlink: int
    uid: int
    gid: int
    size: int
    mtime: float
    atime: float
    ctime: float
    blocks: int

    @classmethod
    def from_stat_result(cls, st: os.stat_result) -> "FileStatus":
        return cls(
            mode=st.st_mode,
            nlink=st.st_nlink,
            uid=st.st_uid,
            gid=st.st_gid,
            size=st.st_size,
            mtime=st.st_mtime,
            atime=st.st_atime,
            ctime=st.st_ctime,
            blocks=st.st_blocks,
        )


@dataclass(frozen=True)
class LongFormatLine:
    mode: str
    nlink: int
    owner: str
    group: str
    size: str
    time: str
    name: str

    def __str__(self) -> str:
        return f"{self.mode} {self.nlink} {self.owner}  {self.group} {self.size} {self.time} {self.name}"


@dataclass(frozen=True)
class FileEntry:
    path: Path
    name: str
    is_dir: bool
    file_status: FileStatus


@dataclass
class DirEntries:
    path: Path
    entries: list[FileEntry]


@dataclass(frozen=True)
class ScanPathsResult:
    entries: list[FileEntry]
    dir_queue: list[Path]
    exit_status: ExitStatus
