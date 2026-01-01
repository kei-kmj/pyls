import os
import stat
from datetime import datetime
from pathlib import Path

import pytest
from freezegun import freeze_time

from pyls.display import (
    c_escape,
    calculate_total_blocks,
    file_type_indicator,
    filetype_char,
    filter_ignored,
    format_entry_name,
    format_line_with_widths,
    format_long_line,
    format_time,
    group_name,
    human_readable_size,
    max_width,
    pad_value,
    permission_string,
    quote_double,
    replace_nonprintable,
    user_name,
)
from pyls.types import LongFormatLine
from tests.conftest import MockOpts, make_file_entry, make_file_status


def test_filetype_char_directory():
    assert filetype_char(stat.S_IFDIR | 0o755) == "d"


def test_filetype_char_symlink():
    assert filetype_char(stat.S_IFLNK | 0o777) == "l"


def test_filetype_char_regular_file():
    assert filetype_char(stat.S_IFREG | 0o644) == "-"


def test_permission_string_rwx_all():
    assert permission_string(0o777) == "rwxrwxrwx"


def test_permission_string_rw_r_r():
    assert permission_string(0o644) == "rw-r--r--"


def test_permission_string_rwx_r_x_r_x():
    assert permission_string(0o755) == "rwxr-xr-x"


def test_permission_string_none():
    assert permission_string(0o000) == "---------"


def test_user_name_resolves_current_user():
    uid = os.getuid()
    result = user_name(uid, numeric=False)
    assert not result.isdigit()


def test_user_name_numeric():
    assert user_name(1000, numeric=True) == "1000"


def test_user_name_unknown_uid_falls_back_to_number():
    assert user_name(99999, numeric=False) == "99999"


def test_group_name_resolves_current_group():
    gid = os.getgid()
    result = group_name(gid, numeric=False)
    assert not result.isdigit()


def test_group_name_numeric():
    assert group_name(1000, numeric=True) == "1000"


def test_group_name_unknown_gid_falls_back_to_number():
    assert group_name(99999, numeric=False) == "99999"


@freeze_time("2025-01-01 12:00:00")
def test_format_time():
    epoch = datetime(2024, 12, 29, 15, 17, 0).timestamp()
    assert format_time(epoch) == "Dec 29 15:17"


def test_format_long_line():
    opts = MockOpts(numeric_uid_gid=True, literal=True)

    entry = make_file_entry(
        Path("test.txt"),
        file_status=make_file_status(
            mode=stat.S_IFREG | 0o644,
            nlink=1,
            uid=1000,
            gid=1000,
            size=256,
            mtime=datetime(2025, 12, 29, 15, 17, 0).timestamp(),
        ),
    )
    line = format_long_line(entry, opts)

    assert line.mode == "-rw-r--r-- "
    assert line.nlink == 1
    assert line.owner == "1000"
    assert line.group == "1000"
    assert line.size == "256"
    assert line.time == "Dec 29 15:17"
    assert line.name == "test.txt"


def test_c_escape_basic():
    assert c_escape("a\nb") == "a\\nb"
    assert c_escape("a\tb") == "a\\tb"


def test_replace_nonprintable_replaces_control_chars_with_question_mark():
    assert replace_nonprintable("a\nb") == "a?b"
    assert replace_nonprintable("a\tb") == "a?b"


def test_quote_double_escapes_quote_and_backslash():
    assert quote_double('a"b') == '"a\\"b"'
    assert quote_double(r"a\b") == '"a\\\\b"'


def test_ignore_filters_matching_names():
    opts = MockOpts(ignore=["*.py"])

    entries = [
        make_file_entry(Path("a.py")),
        make_file_entry(Path("b.txt")),
    ]
    filtered = filter_ignored(entries, opts)
    assert [e.name for e in filtered] == ["b.txt"]


def test_hide_filters_matching_names():
    opts = MockOpts(hide="*.py")

    entries = [
        make_file_entry(Path("a.py")),
        make_file_entry(Path("b.txt")),
    ]
    filtered = filter_ignored(entries, opts)
    assert [e.name for e in filtered] == ["b.txt"]


def test_hide_disabled_by_all():
    opts = MockOpts(hide="*.py", all=True)

    entries = [
        make_file_entry(Path("a.py")),
        make_file_entry(Path("b.txt")),
    ]
    filtered = filter_ignored(entries, opts)
    assert [e.name for e in filtered] == ["a.py", "b.txt"]


def test_hide_disabled_by_almost_all():
    opts = MockOpts(hide="*.py", almost_all=True)

    entries = [
        make_file_entry(Path("a.py")),
        make_file_entry(Path("b.txt")),
    ]
    filtered = filter_ignored(entries, opts)
    assert [e.name for e in filtered] == ["a.py", "b.txt"]


def test_format_entry_name_applies_q():
    opts = MockOpts(hide_control_chars=True)
    e = make_file_entry(Path("x"), "a\nb", False)
    assert format_entry_name(e, opts) == "a?b"


def test_format_entry_name_applies_Q():
    opts = MockOpts(quote_name=True)
    e = make_file_entry(Path("x"), "abc", False)
    assert format_entry_name(e, opts) == '"abc"'


def test_format_entry_name_applies_q_then_Q():
    opts = MockOpts(hide_control_chars=True, quote_name=True)
    e = make_file_entry(Path("x"), "a\nb", False)
    assert format_entry_name(e, opts) == '"a?b"'


def test_N_disables_q_and_Q():
    opts = MockOpts(literal=True, hide_control_chars=True, quote_name=True)
    e = make_file_entry(Path("x"), "a\nb", False)
    assert format_entry_name(e, opts) == "a\nb"


def test_N_only_prints_literal():
    opts = MockOpts(literal=True)
    e = make_file_entry(Path("x"), 'a"b', False)
    assert format_entry_name(e, opts) == 'a"b'


def test_b_wins_over_q():
    opts = MockOpts(escape=True, hide_control_chars=True)
    e = make_file_entry(Path("x"), "a\nb", False)
    assert format_entry_name(e, opts) == "a\\nb"


def test_N_disables_b():
    opts = MockOpts(literal=True, escape=True)
    e = make_file_entry(Path("x"), "a\nb", False)
    assert format_entry_name(e, opts) == "a\nb"


def test_p_appends_slash_only_for_directories():
    opts = MockOpts(indicator_style=True, file_type=True)
    d = make_file_entry(Path("dir"), "dir", True)
    f = make_file_entry(Path("file"), "file", False)

    assert format_entry_name(d, opts) == "dir/"
    assert format_entry_name(f, opts) == "file"


def test_human_readable_size_bytes():
    assert human_readable_size(500) == " 500B"


def test_human_readable_size_kilobytes():
    assert human_readable_size(65444) == "64K"


def test_human_readable_size_megabytes():
    assert human_readable_size(1048576) == " 1.0M"


def test_pad_value_right():
    assert pad_value(42, 5) == "   42"


def test_pad_value_left():
    assert pad_value("hello", 10, right=False) == "hello     "


def test_format_line_with_widths(sample_long_format_line, sample_widths):
    opts = MockOpts()
    result = format_line_with_widths(sample_long_format_line, sample_widths, opts)
    assert "keiko" in result
    assert "staff" in result
    assert "1024" in result


def test_format_line_with_widths_no_owner(sample_long_format_line, sample_widths):
    opts = MockOpts(no_owner=True)
    result = format_line_with_widths(sample_long_format_line, sample_widths, opts)
    assert "keiko" not in result
    assert "staff" in result


def test_format_line_with_widths_no_group(sample_long_format_line, sample_widths):
    opts = MockOpts(no_group=True)
    result = format_line_with_widths(sample_long_format_line, sample_widths, opts)
    assert "keiko" in result
    assert "staff" not in result


def test_calculate_total_blocks():
    entries = [
        make_file_entry(Path("a.txt"), file_status=make_file_status(blocks=8)),
        make_file_entry(Path("b.txt"), file_status=make_file_status(blocks=16)),
        make_file_entry(Path("c.txt"), file_status=make_file_status(blocks=24)),
    ]
    assert calculate_total_blocks(entries) == 48


def test_calculate_total_blocks_empty():
    assert calculate_total_blocks([]) == 0


@pytest.mark.parametrize(
    "key,expected",
    [
        (lambda x: x.nlink, 3),
        (lambda x: x.owner, 14),
        (lambda x: x.size, 4),
    ],
)
def test_max_width(key, expected):
    lines = [
        LongFormatLine(
            mode="-rw-r--r--@",
            nlink=1,
            owner="short",
            group="staff",
            size="100",
            time="Dec 31 12:00",
            name="a.txt",
        ),
        LongFormatLine(
            mode="-rw-r--r--@",
            nlink=100,
            owner="longerusername",
            group="staff",
            size="1024",
            time="Dec 31 12:00",
            name="b.txt",
        ),
        LongFormatLine(
            mode="-rw-r--r--@",
            nlink=10,
            owner="medium",
            group="staff",
            size="50",
            time="Dec 31 12:00",
            name="c.txt",
        ),
    ]
    assert max_width(lines, key) == expected


def test_file_type_indicator_directory_with_classify():
    opts = MockOpts(classify=True)
    entry = make_file_entry(Path("dir"), is_dir=True)
    assert file_type_indicator(entry, opts) == "/"


def test_file_type_indicator_directory_with_p():
    opts = MockOpts(p=True)
    entry = make_file_entry(Path("dir"), is_dir=True)
    assert file_type_indicator(entry, opts) == "/"


def test_file_type_indicator_file_with_classify():
    opts = MockOpts(classify=True)
    entry = make_file_entry(Path("file.txt"), is_dir=False)
    assert file_type_indicator(entry, opts) == ""


def test_file_type_indicator_no_options():
    opts = MockOpts()
    entry = make_file_entry(Path("dir"), is_dir=True)
    assert file_type_indicator(entry, opts) == ""


def test_file_type_indicator_executable_with_classify():
    opts = MockOpts(classify=True)
    entry = make_file_entry(
        Path("script"),
        is_dir=False,
        file_status=make_file_status(mode=stat.S_IFREG | 0o755),
    )
    assert file_type_indicator(entry, opts) == "*"


def test_file_type_indicator_executable_with_file_type():
    opts = MockOpts(file_type=True)
    entry = make_file_entry(
        Path("script"),
        is_dir=False,
        file_status=make_file_status(mode=stat.S_IFREG | 0o755),
    )
    assert file_type_indicator(entry, opts) == ""


@freeze_time("2025-01-01 12:00:00")
def test_format_long_line_with_atime():
    opts = MockOpts(numeric_uid_gid=True, literal=True, time="atime")
    entry = make_file_entry(
        Path("test.txt"),
        file_status=make_file_status(
            mtime=datetime(2024, 12, 1, 10, 0, 0).timestamp(),
            atime=datetime(2024, 12, 15, 15, 30, 0).timestamp(),
            ctime=datetime(2024, 12, 10, 12, 0, 0).timestamp(),
        ),
    )
    line = format_long_line(entry, opts)
    assert line.time == "Dec 15 15:30"


@freeze_time("2025-01-01 12:00:00")
def test_format_long_line_with_ctime():
    opts = MockOpts(numeric_uid_gid=True, literal=True, time="ctime")
    entry = make_file_entry(
        Path("test.txt"),
        file_status=make_file_status(
            mtime=datetime(2024, 12, 1, 10, 0, 0).timestamp(),
            atime=datetime(2024, 12, 15, 15, 30, 0).timestamp(),
            ctime=datetime(2024, 12, 10, 12, 0, 0).timestamp(),
        ),
    )
    line = format_long_line(entry, opts)
    assert line.time == "Dec 10 12:00"


@freeze_time("2025-01-01 12:00:00")
def test_format_long_line_with_default_time():
    opts = MockOpts(numeric_uid_gid=True, literal=True, time=None)
    entry = make_file_entry(
        Path("test.txt"),
        file_status=make_file_status(
            mtime=datetime(2024, 12, 1, 10, 0, 0).timestamp(),
            atime=datetime(2024, 12, 15, 15, 30, 0).timestamp(),
            ctime=datetime(2024, 12, 10, 12, 0, 0).timestamp(),
        ),
    )
    line = format_long_line(entry, opts)
    assert line.time == "Dec 01 10:00"


@freeze_time("2025-01-01 12:00:00")
def test_format_time_within_six_months():
    timestamp = datetime(2024, 10, 15, 14, 30, 0).timestamp()
    assert format_time(timestamp) == "Oct 15 14:30"


@freeze_time("2025-01-01 12:00:00")
def test_format_time_older_than_six_months():
    timestamp = datetime(2024, 3, 15, 10, 0, 0).timestamp()
    assert format_time(timestamp) == "Mar 15  2024"


@freeze_time("2025-01-01 12:00:00")
def test_format_time_future():
    timestamp = datetime(2025, 6, 15, 10, 0, 0).timestamp()
    assert format_time(timestamp) == "Jun 15  2025"