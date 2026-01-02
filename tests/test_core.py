from pathlib import Path

import pytest

from pyls.core import (
    collect_entries,
    gobble_file,
    scan_dir_children,
    should_include,
)
from pyls.types import ExitStatus
from tests.conftest import MockOpts


class Opts:
    directory = False
    all = False
    almost_all = False
    recursive = False


def test_gobble_file_file_not_found(capsys):
    cwd_entries = []

    class Opts:
        pass

    result = gobble_file(Path("/nonexistent/path/to/file"), cwd_entries)

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
        result = gobble_file(restricted / "file", cwd_entries)
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
    opts = MockOpts()
    opts.all = all_flag
    opts.almost_all = almost_all_flag
    assert should_include(name, opts) is expected


def test_scan_dir_children_succeeds_for_existing_dir(sample_000000_dir):
    entries = []
    opts = MockOpts()
    dir_entries, status = scan_dir_children(sample_000000_dir, opts, entries=entries)

    assert status == 0
    assert len(dir_entries.entries) == 12


def test_scan_dir_children_fails_for_nonexistent_dir():
    non_existent_dir = Path("/path/to/nonexistent/dir")
    opts = MockOpts()
    entries = []
    dir_entries, status = scan_dir_children(non_existent_dir, opts, entries=entries)

    assert status == 1


def test_scan_dir_children_fails_for_permission_error(sample_000000_dir, monkeypatch, capsys, mock_permission_error):
    opts = MockOpts()

    monkeypatch.setattr(Path, "iterdir", mock_permission_error)

    entries = []
    dir_entries, status = scan_dir_children(sample_000000_dir, opts, entries)

    assert status == 1
    out = capsys.readouterr().out
    assert "pyls: cannot access" in out


def test_collect_entries_bfs_returns_scan_paths_result_for_existing_dir(sample_000000_dir):
    opts = MockOpts()
    result = collect_entries([sample_000000_dir], opts)

    assert len(result) == 1


def test_collect_entries_bfs_returns_dir_entries_for_existing_file(sample_000000_dir):
    p = sample_000000_dir
    opts = MockOpts()

    result = collect_entries([p], opts)

    assert len(result) == 1
    assert result[0].path == sample_000000_dir
    assert len(result[0].entries) == 12
