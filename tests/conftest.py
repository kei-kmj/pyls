from dataclasses import dataclass, field
from pathlib import Path

import pytest

from pyls.types import FileEntry, FileStatus, LongFormatLine


@dataclass
class MockOpts:
    """テスト用の共通オプションクラス"""

    # 表示
    literal: bool = False
    escape: bool = False
    hide_control_chars: bool = False
    quote_name: bool = False
    directory: bool = False

    # ファイル表示
    numeric_uid_gid: bool = False
    human_readable: bool = False
    no_owner: bool = False
    no_group: bool = False
    recursive: bool = False

    # インジケータ
    indicator_style: bool = False
    classify: bool = False
    file_type: bool = False
    p: bool = False

    # フィルタ
    ignore: list[str] = field(default_factory=list)
    hide: str | bool = False
    all: bool = False
    almost_all: bool = False

    # ソート
    unsorted: bool = False
    reverse: bool = False
    sort: str | None = None
    sort_time: bool = False
    sort_size: bool = False
    sort_extension: bool = False
    sort_version: bool = False
    literal_name: bool = True

    # 時間
    time: str | None = "mtime"

    # カラー
    colorize: bool = False


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
    atime: float = 0.0,
    ctime: float = 0.0,
    blocks: int = 512,
    inode: int = 0,
) -> FileStatus:
    return FileStatus(
        mode=mode,
        nlink=nlink,
        uid=uid,
        gid=gid,
        size=size,
        mtime=mtime,
        atime=atime,
        ctime=ctime,
        blocks=blocks,
        inode=inode,
    )


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


@pytest.fixture
def sample_long_format_line() -> LongFormatLine:
    return LongFormatLine(
        mode="-rw-r--r--@",
        nlink=1,
        owner="keiko",
        group="staff",
        size="1024",
        time="Dec 31 12:00",
        name="test.txt",
    )


@pytest.fixture
def sample_widths() -> dict[str, int]:
    return {"nlink": 1, "owner": 5, "group": 5, "size": 4}


@pytest.fixture
def mock_permission_error(monkeypatch):
    def _raise(self):
        raise PermissionError

    return _raise


@pytest.fixture
def mock_file_not_found_error(monkeypatch):
    def _raise(self):
        raise FileNotFoundError

    return _raise
