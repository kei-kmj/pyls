from pathlib import Path

import pytest

from pyls.core import (
    FileEntry,
    collect_entries_bfs,
    format_entry_name,
    move_dirs_to_pending,
    replace_nonprintable,
    scan_dir_children,
    should_include,
)


class Opts:
    directory = False
    all = False
    almost_all = False
    recursive = False

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


@pytest.mark.parametrize(
    "all_flag, almost_all_flag, name, expected",
    [
        # default: dotfile は除外
        (False, False, "a.txt", True),
        (False, False, ".hidden", False),
        (False, False, ".", False),   # iterdir は返さないが仕様として固定しておく
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

        # -a と -A 同時: -a が勝つ
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



def test_replace_nonprintable_replaces_control_chars_with_question_mark():
    assert replace_nonprintable("a\nb") == "a?b"
    assert replace_nonprintable("a\tb") == "a?b"

def test_format_entry_name_applies_q():
    class Opts:
        hide_control_chars = True

    e = FileEntry(Path("x"), "a\nb", False)
    assert format_entry_name(e, Opts()) == "a?b"