from __future__ import annotations

import fnmatch
import re
from collections.abc import Iterable

from pyls.types import FileEntry


def natural_sort_key(name: str) -> list:
    parts = re.split(r"(\d+)", name.lower())
    return [int(p) if p.isdigit() else p for p in parts]


def should_ignore(name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def filter_ignored(entries: Iterable[FileEntry], opts) -> list[FileEntry]:
    patterns = list(opts.ignore)

    if not (opts.all or opts.almost_all):
        if opts.hide:
            patterns.append(opts.hide)

    if not patterns:
        return list(entries)
    return [e for e in entries if not should_ignore(e.name, patterns)]


def iter_display_entries(entries: list[FileEntry], opts) -> list[FileEntry]:
    if opts.unsorted or opts.sort == "none":
        return list(entries)

    if opts.sort_time or opts.sort == "time":
        return sorted(entries, key=lambda e: e.file_status.mtime, reverse=not opts.reverse)

    if opts.sort_size or opts.sort == "size":
        return sorted(entries, key=lambda e: e.file_status.size, reverse=not opts.reverse)

    if opts.sort_extension or opts.sort == "extension":

        def ext_key(e: FileEntry) -> tuple[str, str]:
            name = e.name
            if "." in name:
                extension = name.rsplit(".", 1)[1].lower()
            else:
                extension = ""
            return extension, name.lower()

        return sorted(entries, key=ext_key, reverse=opts.reverse)

    if opts.sort_version or opts.sort == "version":
        return sorted(entries, key=lambda e: natural_sort_key(e.name), reverse=opts.reverse)

    return sorted(entries, key=lambda e: e.name.lower(), reverse=opts.reverse)