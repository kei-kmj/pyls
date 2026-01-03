from pyls.cli import build_parser
from pyls.core import scan_dir_children
from pyls.output import print_newline_except_last, print_directory, print_files, print_subdirs_recursively, \
    print_columns, print_entries


def test_print_entries_one_column(sample_000000_dir, capsys):
    args = build_parser().parse_args(["-1"])
    dir_entries, _ = scan_dir_children(sample_000000_dir, args, entries=[])

    print_entries(dir_entries.entries, args)

    out = capsys.readouterr().out
    lines = out.strip().split("\n")
    # 1行1ファイルになっている
    assert len(lines) == len(dir_entries.entries)
    assert "dir_a" in lines
    assert "dir_b" in lines


def test_print_files_single_file(sample_000000_dir, capsys):
    args = build_parser().parse_args([])
    files = [sample_000000_dir / "file_0000.txt"]

    print_files(files, args)

    out = capsys.readouterr().out
    assert "file_0000.txt" in out


def test_print_files_multiple_files(sample_000000_dir, capsys):
    args = build_parser().parse_args([])
    files = [
        sample_000000_dir / "file_0000.txt",
        sample_000000_dir / "file_0001.txt",
    ]

    print_files(files, args)

    out = capsys.readouterr().out
    assert "file_0000.txt" in out
    assert "file_0001.txt" in out


def test_print_files_long_format(sample_000000_dir, capsys):
    args = build_parser().parse_args(["-l"])
    files = [sample_000000_dir / "file_0000.txt"]

    print_files(files, args)

    out = capsys.readouterr().out
    assert "file_0000.txt" in out
    assert "-rw" in out


def test_print_directory_with_header(sample_000000_dir, capsys):
    args = build_parser().parse_args([])

    print_directory(sample_000000_dir, args, show_header=True)

    out = capsys.readouterr().out
    assert f"{sample_000000_dir}:" in out
    assert "dir_a" in out
    assert "dir_b" in out


def test_print_directory_without_header(sample_000000_dir, capsys):
    args = build_parser().parse_args([])

    print_directory(sample_000000_dir, args, show_header=False)

    out = capsys.readouterr().out
    assert f"{sample_000000_dir}:" not in out
    assert "dir_a" in out


def test_print_directory_returns_subdirs(sample_000000_dir):
    args = build_parser().parse_args([])

    subdirs = print_directory(sample_000000_dir, args, show_header=False)

    subdir_names = [s.name for s in subdirs]
    assert "dir_a" in subdir_names
    assert "dir_b" in subdir_names


def test_print_directory_excludes_dot_dirs(sample_000000_dir):
    args = build_parser().parse_args(["-a"])  # show . and ..

    subdirs = print_directory(sample_000000_dir, args, show_header=False)

    subdir_names = [s.name for s in subdirs]
    assert "." not in subdir_names
    assert ".." not in subdir_names


def test_print_newline_except_last_prints_newline_when_not_last(capsys):
    print_newline_except_last(0, 3)
    out = capsys.readouterr().out
    assert out == "\n"


def test_print_newline_except_last_prints_nothing_when_last(capsys):
    print_newline_except_last(2, 3)
    out = capsys.readouterr().out
    assert out == ""


def test_print_newline_except_last_single_item(capsys):
    print_newline_except_last(0, 1)
    out = capsys.readouterr().out
    assert out == ""


def test_print_subdirs_recursively_with_dot_prefix(sample_000000_dir, capsys):
    args = build_parser().parse_args(["-R"])
    args.paths = ["."]
    subdirs = [sample_000000_dir / "dir_a"]

    print_subdirs_recursively(subdirs, args)

    out = capsys.readouterr().out
    assert "./" in out


def test_print_subdirs_recursively_without_dot_prefix(sample_000000_dir, capsys):
    args = build_parser().parse_args(["-R"])
    args.paths = ["test_fixture"]
    subdirs = [sample_000000_dir / "dir_a"]

    print_subdirs_recursively(subdirs, args)

    out = capsys.readouterr().out
    assert out.startswith("./") is False


def test_print_subdirs_recursively_shows_contents(sample_000000_dir, capsys):
    args = build_parser().parse_args(["-R"])
    args.paths = ["test_fixture"]
    subdirs = [sample_000000_dir / "dir_a"]

    print_subdirs_recursively(subdirs, args)

    out = capsys.readouterr().out
    assert "a_0000.txt" in out


def test_print_subdirs_recursively_multiple_dirs(sample_000000_dir, capsys):
    args = build_parser().parse_args(["-R"])
    args.paths = ["test_fixture"]
    subdirs = [
        sample_000000_dir / "dir_a",
        sample_000000_dir / "dir_b",
    ]

    print_subdirs_recursively(subdirs, args)

    out = capsys.readouterr().out
    assert "dir_a" in out
    assert "dir_b" in out
    assert "a_0000.txt" in out
    assert "b_0000.txt" in out


def test_print_columns_empty_list(capsys):
    print_columns([], terminal_width=80)

    out = capsys.readouterr().out
    assert out == ""