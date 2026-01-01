import shutil


def print_newline_except_last(index: int, total: int) -> None:
    print("\n" if index + 1 < total else "", end="")


def get_terminal_width() -> int:
    return shutil.get_terminal_size().columns


def print_columns(names: list[str], terminal_width: int, tab_size: int = 8) -> None:
    """ファイル名を横並びで表示"""
    if not names:
        return

    max_len = max(len(name) for name in names)
    col_width = ((max_len // tab_size) + 1) * tab_size

    # 収まる最大の列数を計算
    columns = max(1, terminal_width // col_width)

    # 行数を計算
    rows = (len(names) + columns - 1) // columns

    # 縦方向に表示
    for row in range(rows):
        for col in range(columns):
            idx = col * rows + row
            if idx < len(names):
                print(names[idx].ljust(col_width), end="")
        print_newline_except_last(row, rows)
