from pyls.types import LongFormatLine


def test_long_format_line_str():
    line = LongFormatLine(
        mode="-rw-r--r--",
        nlink=1,
        owner="keiko",
        group="staff",
        size="256",
        time="Dec 29 15:17",
        name="test.txt",
    )

    assert str(line) == "-rw-r--r-- 1 keiko  staff 256 Dec 29 15:17 test.txt"
