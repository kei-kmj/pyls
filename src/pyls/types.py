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
    dir_queue: list[Path]
    exit_status: ExitStatus