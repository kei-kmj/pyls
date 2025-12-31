from pathlib import Path

import pytest

from pyls.types import FileStatus, FileEntry


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def sample_000000_dir(repo_root: Path) -> Path:
    return repo_root / "test_fixture" / "sample_000000"


def make_file_status(
    mode: int = 0o100644,
    nlink: int = 1,
    uid: int = 1000,
    gid: int = 1000,
    size: int = 0,
    mtime: float = 0.0,
) -> FileStatus:
    return FileStatus(mode=mode, nlink=nlink, uid=uid, gid=gid, size=size, mtime=mtime)


def make_file_entry(
    path: Path,
    name: str | None = None,
    is_dir: bool = False,
    file_status: FileStatus | None = None,
) -> FileEntry:
    return FileEntry(
        path=path,
        name=name or path.name,
        is_dir=is_dir,
        file_status=file_status or make_file_status(),
    )