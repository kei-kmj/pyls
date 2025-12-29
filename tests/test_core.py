from pathlib import Path

from pyls.core import collect_entries_bfs, move_dirs_to_pending, scan_dir_children


class Opts:
    directory = False

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

    entries = []
    assert scan_dir_children(sample_000000_dir, DirOpts(), entries) == 0

    pending_queue = []
    move_dirs_to_pending(entries, pending_queue, DirOpts())

    assert pending_queue == []
    assert {e.name for e in entries} >= {"dir_a", "dir_b"}


def test_collect_entries_bfs_returns_scan_paths_result_for_existing_dir(sample_000000_dir):
    result = collect_entries_bfs([sample_000000_dir], Opts())

    assert result.exit_status == 0
    assert sample_000000_dir in result.pending_dirs

def test_collect_entries_bfs_returns_scan_paths_result_for_existing_file(sample_000000_dir):
    p = sample_000000_dir / "file_0000.txt"

    result = collect_entries_bfs([p], Opts())

    assert result.exit_status == 0
    assert result.pending_dirs == []
    assert {e.name for e in result.entries} == {"file_0000.txt"}