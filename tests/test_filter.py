
from pathlib import Path

from pyls.filter import filter_ignored, iter_display_entries
from conftest import MockOpts, make_file_entry, make_file_status


def test_ignore_filters_matching_names():
    opts = MockOpts(ignore=["*.py"])

    entries = [
        make_file_entry(Path("a.py")),
        make_file_entry(Path("b1.txt")),
    ]
    filtered = filter_ignored(entries, opts)
    assert [e.name for e in filtered] == ["b1.txt"]


def test_hide_filters_matching_names():
    opts = MockOpts(hide="*.py")

    entries = [
        make_file_entry(Path("a.py")),
        make_file_entry(Path("b1.txt")),
    ]
    filtered = filter_ignored(entries, opts)
    assert [e.name for e in filtered] == ["b1.txt"]


def test_hide_disabled_by_all():
    opts = MockOpts(hide="*.py", all=True)

    entries = [
        make_file_entry(Path("a.py")),
        make_file_entry(Path("b1.txt")),
    ]
    filtered = filter_ignored(entries, opts)
    assert [e.name for e in filtered] == ["a.py", "b1.txt"]


def test_hide_disabled_by_almost_all():
    opts = MockOpts(hide="*.py", almost_all=True)

    entries = [
        make_file_entry(Path("a.py")),
        make_file_entry(Path("b1.txt")),
    ]
    filtered = filter_ignored(entries, opts)
    assert [e.name for e in filtered] == ["a.py", "b1.txt"]


def test_iter_display_entries_sort_by_name():
    opts = MockOpts()
    entries = [
        make_file_entry(Path("c.txt")),
        make_file_entry(Path("a.txt")),
        make_file_entry(Path("b1.txt")),
    ]
    result = iter_display_entries(entries, opts)
    assert [e.name for e in result] == ["a.txt", "b1.txt", "c.txt"]


def test_iter_display_entries_sort_by_name_case_insensitive():
    opts = MockOpts()
    entries = [
        make_file_entry(Path("B.txt")),
        make_file_entry(Path("a.txt")),
        make_file_entry(Path("c.txt")),
    ]
    result = iter_display_entries(entries, opts)
    assert [e.name for e in result] == ["a.txt", "B.txt", "c.txt"]


def test_iter_display_entries_sort_by_time():
    opts = MockOpts(sort_time=True)
    entries = [
        make_file_entry(Path("old.txt"), file_status=make_file_status(mtime=1000.0)),
        make_file_entry(Path("new.txt"), file_status=make_file_status(mtime=3000.0)),
        make_file_entry(Path("mid.txt"), file_status=make_file_status(mtime=2000.0)),
    ]
    result = iter_display_entries(entries, opts)
    assert [e.name for e in result] == ["new.txt", "mid.txt", "old.txt"]


def test_iter_display_entries_sort_by_size():
    opts = MockOpts(sort_size=True)
    entries = [
        make_file_entry(Path("small.txt"), file_status=make_file_status(size=100)),
        make_file_entry(Path("large.txt"), file_status=make_file_status(size=1000)),
        make_file_entry(Path("medium.txt"), file_status=make_file_status(size=500)),
    ]
    result = iter_display_entries(entries, opts)
    assert [e.name for e in result] == ["large.txt", "medium.txt", "small.txt"]


def test_iter_display_entries_sort_by_size_reverse():
    opts = MockOpts(sort_size=True, reverse=True)
    entries = [
        make_file_entry(Path("small.txt"), file_status=make_file_status(size=100)),
        make_file_entry(Path("large.txt"), file_status=make_file_status(size=1000)),
        make_file_entry(Path("medium.txt"), file_status=make_file_status(size=500)),
    ]
    result = iter_display_entries(entries, opts)
    assert [e.name for e in result] == ["small.txt", "medium.txt", "large.txt"]


def test_iter_display_entries_unsorted():
    opts = MockOpts(unsorted=True)
    entries = [
        make_file_entry(Path("c.txt")),
        make_file_entry(Path("a.txt")),
        make_file_entry(Path("b1.txt")),
    ]
    result = iter_display_entries(entries, opts)
    assert [e.name for e in result] == ["c.txt", "a.txt", "b1.txt"]


def test_iter_display_entries_sort_by_extension():
    opts = MockOpts(sort_extension=True)
    entries = [
        make_file_entry(Path("a.txt")),
        make_file_entry(Path("b.py")),
        make_file_entry(Path("c.md")),
        make_file_entry(Path("no_ext")),
    ]
    result = iter_display_entries(entries, opts)
    # 拡張子なし → md → py → txt
    assert [e.name for e in result] == ["no_ext", "c.md", "b.py", "a.txt"]


def test_iter_display_entries_sort_by_version():
    opts = MockOpts(sort_version=True)
    entries = [
        make_file_entry(Path("file10.txt")),
        make_file_entry(Path("file2.txt")),
        make_file_entry(Path("file1.txt")),
        make_file_entry(Path("file20.txt")),
    ]
    result = iter_display_entries(entries, opts)
    # 自然順: 1 → 2 → 10 → 20
    assert [e.name for e in result] == ["file1.txt", "file2.txt", "file10.txt", "file20.txt"]
