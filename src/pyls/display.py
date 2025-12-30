def c_escape(s: str) -> str:
    output: list[str] = []

    for ch in s:
        if ch == "\n":
            output.append("\\n")
            continue
        if ch == "\t":
            output.append("\\t")
            continue
        if ch == "\r":
            output.append("\\r")
            continue

        if ch == "\\":
            output.append("\\\\")
            continue

        if ch.isprintable():
            output.append(ch)
            continue

        code = ord(ch)
        if code <= 0xFF:
            output.append(f"\\x{code:02x}")
        elif code <= 0xFFFF:
            output.append(f"\\u{code:04x}")
        else:
            output.append(f"\\U{code:08x}")

    return "".join(output)



def replace_nonprintable(s: str) -> str:
    return "".join(ch if ch.isprintable() else "?" for ch in s)


def iter_display_entries(entries: list[FileEntry], opts) -> list[FileEntry]:
    if opts.unsorted:
        return list(entries)
    return sorted(entries, key=lambda e: e.name, reverse=opts.reverse)


def quote_double(s: str) -> str:
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def format_entry_name(entry: FileEntry, opts) -> str:

    if opts.literal:
        return entry.name

    name = entry.name

    if opts.escape:
        name = c_escape(name)

    if opts.hide_control_chars:
        name = replace_nonprintable(name)

    if opts.quote_name:
        name = quote_double(name)

    if opts.indicator_style and entry.is_dir:
        name += "/"

    return name
