from pathlib import Path

from pyls.display import (
    c_escape,
    replace_nonprintable,
    quote_double,
    format_entry_name,
)
from pyls.types import FileEntry


# c_escape tests

def test_c_escape_basic():
    assert c_escape("a\nb") == "a\\nb"
    assert c_escape("a\tb") == "a\\tb"


# replace_nonprintable tests

def test_replace_nonprintable_replaces_control_chars_with_question_mark():
    assert replace_nonprintable("a\nb") == "a?b"
    assert replace_nonprintable("a\tb") == "a?b"


# quote_double tests

def test_quote_double_escapes_quote_and_backslash():
    assert quote_double('a"b') == '"a\\"b"'
    assert quote_double(r"a\b") == '"a\\\\b"'


# format_entry_name tests

def test_format_entry_name_applies_q():
    class Opts:
        literal = False
        hide_control_chars = True
        quote_name = False
        escape = False
        indicator_style = False

    e = FileEntry(Path("x"), "a\nb", False)
    assert format_entry_name(e, Opts()) == "a?b"


def test_format_entry_name_applies_Q():
    class Opts:
        literal = False
        hide_control_chars = False
        quote_name = True
        escape = False
        indicator_style = False

    e = FileEntry(Path("x"), "abc", False)
    assert format_entry_name(e, Opts()) == '"abc"'


def test_format_entry_name_applies_q_then_Q():
    class Opts:
        literal = False
        hide_control_chars = True
        quote_name = True
        escape = False
        indicator_style = False

    e = FileEntry(Path("x"), "a\nb", False)
    assert format_entry_name(e, Opts()) == '"a?b"'


def test_N_disables_q_and_Q():
    class Opts:
        literal = True
        hide_control_chars = True
        quote_name = True

    e = FileEntry(Path("x"), "a\nb", False)
    assert format_entry_name(e, Opts()) == "a\nb"


def test_N_only_prints_literal():
    class Opts:
        literal = True
        hide_control_chars = False
        quote_name = False

    e = FileEntry(Path("x"), 'a"b', False)
    assert format_entry_name(e, Opts()) == 'a"b'


def test_b_wins_over_q():
    class Opts:
        literal = False
        escape = True
        hide_control_chars = True
        quote_name = False
        indicator_style = False


    e = FileEntry(Path("x"), "a\nb", False)
    assert format_entry_name(e, Opts()) == "a\\nb"

def test_N_disables_b():
    class Opts:
        literal = True
        escape = True
        hide_control_chars = False
        quote_name = False

    e = FileEntry(Path("x"), "a\nb", False)
    assert format_entry_name(e, Opts()) == "a\nb"


def test_p_appends_slash_only_for_directories():
    class Opts:
        literal = False
        escape = False
        hide_control_chars = False
        quote_name = False
        indicator_style = True

    d = FileEntry(Path("dir"), "dir", True)
    f = FileEntry(Path("file"), "file", False)

    assert format_entry_name(d, Opts()) == "dir/"
    assert format_entry_name(f, Opts()) == "file"