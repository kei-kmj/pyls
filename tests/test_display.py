import os
import stat
from datetime import datetime
from pathlib import Path

from pyls.display import (
    c_escape,
    filter_ignored,
    format_entry_name,
    quote_double,
    replace_nonprintable, filetype_char, permission_string, format_mtime, format_long_line, group_name, user_name,
)
from tests.conftest import make_file_entry, make_file_status


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


def test_format_mtime():
    # 2024-12-29 15:17:00
    epoch = datetime(2024, 12, 29, 15, 17, 0).timestamp()
    assert format_mtime(epoch) == "Dec 29 15:17"


def test_format_long_line():
    class Opts:
        numeric_uid_gid = True
        literal = True
        escape = False
        hide_control_chars = False
        quote_name = False
        p = False

    entry = make_file_entry(
        Path("test.txt"),
        file_status=make_file_status(
            mode=stat.S_IFREG | 0o644,
            nlink=1,
            uid=1000,
            gid=1000,
            size=256,
            mtime=datetime(2024, 12, 29, 15, 17, 0).timestamp(),
        ),
    )
    line = format_long_line(entry, Opts())

    assert line.mode == "-rw-r--r-- "
    assert line.nlink == 1
    assert line.owner == "1000"
    assert line.group == "1000"
    assert line.size == 256
    assert line.mtime == "Dec 29 15:17"
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
    class Opts:
        ignore = ["*.py"]
        unsorted = False
        reverse = False
        literal_name = True
        escape = False
        hide_control_chars = False
        quote_name = False
        p = False

    entries = [
        make_file_entry(Path("a.py")),
        make_file_entry(Path("b.txt")),
    ]
    filtered = filter_ignored(entries, Opts())
    assert [e.name for e in filtered] == ["b.txt"]


def test_format_entry_name_applies_q():
    class Opts:
        literal = False
        hide_control_chars = True
        quote_name = False
        escape = False
        indicator_style = False

    e = make_file_entry(Path("x"), "a\nb", False)
    assert format_entry_name(e, Opts()) == "a?b"


def test_format_entry_name_applies_Q():
    class Opts:
        literal = False
        hide_control_chars = False
        quote_name = True
        escape = False
        indicator_style = False

    e = make_file_entry(Path("x"), "abc", False)
    assert format_entry_name(e, Opts()) == '"abc"'


def test_format_entry_name_applies_q_then_Q():
    class Opts:
        literal = False
        hide_control_chars = True
        quote_name = True
        escape = False
        indicator_style = False

    e = make_file_entry(Path("x"), "a\nb", False)
    assert format_entry_name(e, Opts()) == '"a?b"'


def test_N_disables_q_and_Q():
    class Opts:
        literal = True
        hide_control_chars = True
        quote_name = True

    e = make_file_entry(Path("x"), "a\nb", False)
    assert format_entry_name(e, Opts()) == "a\nb"


def test_N_only_prints_literal():
    class Opts:
        literal = True
        hide_control_chars = False
        quote_name = False

    e = make_file_entry(Path("x"), 'a"b', False)
    assert format_entry_name(e, Opts()) == 'a"b'


def test_b_wins_over_q():
    class Opts:
        literal = False
        escape = True
        hide_control_chars = True
        quote_name = False
        indicator_style = False


    e = make_file_entry(Path("x"), "a\nb", False)
    assert format_entry_name(e, Opts()) == "a\\nb"


def test_N_disables_b():
    class Opts:
        literal = True
        escape = True
        hide_control_chars = False
        quote_name = False

    e = make_file_entry(Path("x"), "a\nb", False)
    assert format_entry_name(e, Opts()) == "a\nb"


def test_p_appends_slash_only_for_directories():
    class Opts:
        literal = False
        escape = False
        hide_control_chars = False
        quote_name = False
        indicator_style = True

    d = make_file_entry(Path("dir"), "dir", True)
    f = make_file_entry(Path("file"), "file", False)

    assert format_entry_name(d, Opts()) == "dir/"
    assert format_entry_name(f, Opts()) == "file"
