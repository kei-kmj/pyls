from pathlib import Path

import pytest

from pyls.core import (
    collect_entries,
    gobble_file,
    scan_dir_children,
    should_include, classify_paths,
)
from pyls.types import ExitStatus
from conftest import MockOpts


def test_gobble_file_file_not_found(capsys):
    cwd_entries = []

    result = gobble_file(Path("/nonexistent/path/to/file"), cwd_entries)

    assert result == ExitStatus.ERROR
    assert cwd_entries == []
    captured = capsys.readouterr()
    assert "No such file or directory" in captured.out


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


def test_scan_dir_children_succeeds_for_existing_dir(sample_00_dir):
    entries = []
    opts = MockOpts()
    dir_entries, status = scan_dir_children(sample_00_dir, opts, entries=entries)

    assert status == 0
    assert len(dir_entries.entries) == 12


def test_scan_dir_children_fails_for_nonexistent_dir():
    non_existent_dir = Path("/path/to/nonexistent/dir")
    opts = MockOpts()
    entries = []
    dir_entries, status = scan_dir_children(non_existent_dir, opts, entries=entries)

    assert status == 1


def test_scan_dir_children_fails_for_permission_error(sample_00_dir, monkeypatch, capsys, mock_permission_error):
    opts = MockOpts()

    monkeypatch.setattr(Path, "iterdir", mock_permission_error)

    entries = []
    dir_entries, status = scan_dir_children(sample_00_dir, opts, entries)

    assert status == 1
    out = capsys.readouterr().out
    assert "pyls: cannot access" in out


def test_collect_entries_bfs_returns_scan_paths_result_for_existing_dir(sample_00_dir):
    opts = MockOpts()
    result = collect_entries([sample_00_dir], opts)

    assert len(result) == 1


def test_collect_entries_bfs_returns_dir_entries_for_existing_file(sample_00_dir):
    p = sample_00_dir
    opts = MockOpts()

    result = collect_entries([p], opts)

    assert len(result) == 1
    assert result[0].path == sample_00_dir
    assert len(result[0].entries) == 12


def test_classify_paths_only_files(sample_00_dir):
    opts = MockOpts()
    paths = [
        str(sample_00_dir / "file_0000.txt"),
        str(sample_00_dir / "file_0001.txt"),
    ]

    files, dirs = classify_paths(paths, opts)

    assert len(files) == 2
    assert len(dirs) == 0


def test_classify_paths_only_dirs(sample_00_dir):
    opts = MockOpts()
    paths = [
        str(sample_00_dir / "dir_a"),
        str(sample_00_dir / "dir_b"),
    ]

    files, dirs = classify_paths(paths, opts)

    assert len(files) == 0
    assert len(dirs) == 2


def test_classify_paths_mixed(sample_00_dir):
    opts = MockOpts()
    paths = [
        str(sample_00_dir / "file_0000.txt"),
        str(sample_00_dir / "dir_a"),
    ]

    files, dirs = classify_paths(paths, opts)

    assert len(files) == 1
    assert len(dirs) == 1
    assert files[0].name == "file_0000.txt"
    assert dirs[0].name == "dir_a"


def test_classify_paths_empty():
    opts = MockOpts()
    files, dirs = classify_paths([], opts)

    assert files == []
    assert dirs == []


