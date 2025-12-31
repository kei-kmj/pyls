from pathlib import Path

import pytest

from pyls.core import (
    collect_entries_bfs,
    extract_dirs_from_files,
    gobble_file,
    move_dirs_to_pending,
    scan_dir_children,
    should_include,
)
from pyls.types import ExitStatus
from tests.conftest import make_file_entry


class Opts:
    directory = False
    all = False
    almost_all = False
    recursive = False


def test_gobble_file_file_not_found(capsys):
    cwd_entries = []

    class Opts:
        pass

    result = gobble_file(Path("/nonexistent/path/to/file"), Opts(), cwd_entries)

    assert result == ExitStatus.ERROR
    assert cwd_entries == []
    captured = capsys.readouterr()
    assert "No such file or directory" in captured.out


def test_gobble_file_permission_denied(capsys, tmp_path):
    # パーミッションなしのファイルを作成
    restricted = tmp_path / "restricted"
    restricted.mkdir()
    restricted.chmod(0o000)

    cwd_entries = []

    class Opts:
        pass

    try:
        result = gobble_file(restricted / "file", Opts(), cwd_entries)
        assert result == ExitStatus.ERROR
        captured = capsys.readouterr()
        assert "Permission denied" in captured.out
    finally:
        # 後片付け
        restricted.chmod(0o755)


@pytest.mark.parametrize(
    "all_flag, almost_all_flag, name, expected",
    [
        # default: dotfile は除外
        (False, False, "a.txt", True),
        (False, False, ".hidden", False),
        (False, False, ".", False),  # iterdir は返さないが仕様として固定しておく
        (False, False, "..", False),
        # -A: dotfile は含める（ただし . と .. は除外）
        (False, True, "a.txt", True),
        (False, True, ".hidden", True),
        (False, True, ".", False),
        (False, True, "..", False),
        # -a: すべて含める（-A より優先）
        (True, False, "a.txt", True),
        (True, False, ".hidden", True),
        (True, False, ".", True),
        (True, False, "..", True),
        # -a -A: すべて含める（-a が優先）
        (True, True, ".", True),
        (True, True, "..", True),
        (True, True, ".hidden", True),
    ],
)
def test_should_include(all_flag, almost_all_flag, name, expected):
    opts = Opts()
    opts.all = all_flag
    opts.almost_all = almost_all_flag
    assert should_include(name, opts) is expected


def test_scan_dir_children_succeeds_for_existing_dir(sample_000000_dir):
    entries = []
    status = scan_dir_children(sample_000000_dir, Opts(), entries=entries)

    assert status == 0
    assert len(entries) == 12


def test_scan_dir_children_fails_for_nonexistent_dir():
    non_existent_dir = Path("/path/to/nonexistent/dir")
    entries = []
    status = scan_dir_children(non_existent_dir, Opts(), entries=entries)

    assert status == 1


def test_scan_dir_children_fails_for_permission_error(sample_000000_dir, monkeypatch, capsys):
    def _raise_permission_error(self):
        raise PermissionError

    monkeypatch.setattr(Path, "iterdir", _raise_permission_error)

    entries = []
    status = scan_dir_children(sample_000000_dir, Opts(), entries)

    assert status == 1
    out = capsys.readouterr().out
    assert "pyls: cannot access" in out


def test_extract_dirs_from_files_does_nothing_when_directory_opt_is_true():
    class Opts:
        directory = True

    cwd_entries = [
        make_file_entry(Path("dir1"), is_dir=True),
        make_file_entry(Path("file.txt"), is_dir=False),
    ]
    pending_dirs = []

    extract_dirs_from_files(cwd_entries, pending_dirs, Opts())

    # 何も変わらない
    assert len(cwd_entries) == 2
    assert pending_dirs == []


def test_collect_entries_bfs_returns_scan_paths_result_for_existing_dir(sample_000000_dir):
    result = collect_entries_bfs([sample_000000_dir], Opts())

    assert result.exit_status == 0
    assert sample_000000_dir in result.dir_queue


def test_collect_entries_bfs_returns_scan_paths_result_for_existing_file(sample_000000_dir):
    p = sample_000000_dir / "file_0000.txt"

    result = collect_entries_bfs([p], Opts())

    assert result.exit_status == 0
    assert result.dir_queue == []
    assert {e.name for e in result.entries} == {"file_0000.txt"}


def test_move_dirs_to_pending_moves_dirs_and_keeps_files(sample_000000_dir):
    entries = []
    assert scan_dir_children(sample_000000_dir, Opts(), entries) == 0

    pending_dirs = []
    move_dirs_to_pending(entries, pending_dirs, Opts())
    assert len(pending_dirs) == 2
    assert {p.name for p in pending_dirs} == {"dir_a", "dir_b"}
    assert all(not e.is_dir for e in entries)
    assert len(entries) == 10


def test_move_dirs_to_pending_does_nothing_when_directory_opt_is_true(sample_000000_dir):
    class DirOpts:
        directory = True
        all = True

    entries = []
    assert scan_dir_children(sample_000000_dir, DirOpts(), entries) == 0

    pending_queue = []
    move_dirs_to_pending(entries, pending_queue, DirOpts())

    assert pending_queue == []
    assert {e.name for e in entries} >= {"dir_a", "dir_b"}


def test_extract_dirs_from_files():
    cwd_entries = [
        make_file_entry(Path("dir1"), is_dir=True),
        make_file_entry(Path("file1.txt"), is_dir=False),
        make_file_entry(Path("dir2"), is_dir=True),
        make_file_entry(Path("file2.txt"), is_dir=False),
    ]
    pending_dirs = []

    class Opts:
        directory = False

    extract_dirs_from_files(cwd_entries, pending_dirs, Opts())

    assert len(pending_dirs) == 2
    assert Path("dir1") in pending_dirs
    assert Path("dir2") in pending_dirs

    assert len(cwd_entries) == 2
    assert all(not e.is_dir for e in cwd_entries)


def test_extract_dirs_from_files_with_directory_opt():
    cwd_entries = [
        make_file_entry(Path("dir1"), is_dir=True),
        make_file_entry(Path("file1.txt"), is_dir=False),
    ]
    pending_dirs = []

    class Opts:
        directory = True

    extract_dirs_from_files(cwd_entries, pending_dirs, Opts())

    assert len(cwd_entries) == 2
    assert len(pending_dirs) == 0
