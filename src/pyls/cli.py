import argparse


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pyls",
        usage = "%(prog)s [OPTION]... [FILE]...",
        add_help = False,
    )
    p.add_argument("--help", action="help", help="display this help and exit")
    p.add_argument("--version", action="store_true", help="output version information and exit")

    p.add_argument("-a", "--all", action="store_true", help="do not ignore entries starting with .")
    p.add_argument("-A", "--almost-all", action="store_true", help="do not list implied . and ..")
    p.add_argument("-b", "--escape", action="store_true", help="print C-style escapes for nongraphic characters")
    p.add_argument("-d", "--directory", action="store_true", help="list directories themselves, not their contents")
    p.add_argument("--file-type", action="store_true", help="likewise, except do not append '*'")
    p.add_argument("-F", "--classify", action="store_true", help="append indicator (one of */=>@|) to entries")
    p.add_argument("-g", "--no-owner", action="store_true", help="like -l, but do not list owner information")
    p.add_argument(
        "-h",
        "--human-readable",
        action="store_true",
        help="with -l, print sizes in human readable format (e.g., 1K 234M 2G)")
    p.add_argument("--hide", metavar="PATTERN", action="store", help="do not list implied entries matching PATTERN")
    p.add_argument("-i", "--inode", action="store_true", help="print the index number of each file")
    p.add_argument(
        "-I",
        "--ignore",
        metavar="PATTERN",
        action="append",
        default=[],
        help="do not list implied entries matching PATTERN")
    p.add_argument("-l", dest="long", action="store_true", help="use a long listing format")
    p.add_argument("-n", "--numeric-uid-gid", action="store_true", help="like -l, but list numeric user and group IDs")
    p.add_argument("-N", "--literal", action="store_true", help="print entry names without quoting or escaping")
    p.add_argument("-o", "--no-group", action="store_true", help="like -l, but do not list group information")
    p.add_argument("-p", action="store_true", help="append / indicator to directories")
    p.add_argument(
        "--indicator-style",
        metavar="WORD",
        action="store",
        help="append indicator with style WORD to entry names")
    p.add_argument("-q", "--hide-control-chars", action="store_true", help="print ? instead of nongraphic characters")
    p.add_argument("-Q", "--quote-name", action="store_true", help="enclose entry names in double quotes")
    p.add_argument("-r", "--reverse", action="store_true", help="reverse order while sorting")
    p.add_argument("-R", "--recursive", action="store_true", help="list subdirectories recursively")
    p.add_argument("-s", "--size", action="store_true", help="print the allocated size of each file, in blocks")
    p.add_argument("--sort", metavar="WORD", action="store", help="store_true")
    p.add_argument("-S", "--sort-size", action="store_true", help="sort by file size, largest first")
    p.add_argument("-t", "--sort-time", action="store_true", help="sort by modification time, newest first")
    p.add_argument(
        "--time",
        metavar="WORD",
        action="store",
        help="with --sort=time, sort by WORD instead of modification time: atime or ctime")
    p.add_argument(
        "-T",
        "--tabsize",
        metavar="COLS",
        type=int,
        action="store",
        help="assume tab stops at each COLS instead of 8")
    p.add_argument(
        "-U",
        "--sort-untimed",
        dest="unsorted",
        action="store_true",
        help="do not sort; list entries in directory order")
    p.add_argument("-v", "--sort-version", action="store_true", help="natural sort of (version) numbers within text")
    p.add_argument("-X", "--sort-extension", action="store_true", help="sort by file extension")
    p.add_argument(
        "-w",
        "--width",
        metavar="COLS",
        type=int,
        action="store",
        help="assume screen width instead of current value")
    p.add_argument("-Z", "--context", action="store_true", help="print any SELinux security context of each file")
    p.add_argument("-1", "--one-column", action="store_true", help="list one file per line")
    p.add_argument("paths", nargs="*")
    return p