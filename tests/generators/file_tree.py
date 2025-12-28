"""
Create fixed test fixtures for pyls.

Env vars:
  ROOT  : output root dir (default: ./test_fixture)
  SAMPLES: number of SAMPLES (default: 1)
  RESET: if "1", remove ROOT before creating (default: 0)

Fixed structure per sample:
  sample_000000/
    dir_a/ (5 files: a_0000..a_0004)
    dir_b/ (8 files: b_0000..b_0007)
    (10 files: file_0000..file_0009)
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Final

# Fixed spec
TOP_FILES: Final[int] = 10
DIR_A_FILES: Final[int] = 5
DIR_B_FILES: Final[int] = 8


def env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None or v.strip() == "":
        return default
    try:
        n = int(v)
    except ValueError as e:
        raise SystemExit(f"{name} must be int, got: {v!r}") from e
    if n < 0:
        raise SystemExit(f"{name} must be >= 0, got: {n}")
    return n


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # empty file, update mtime if exists
    path.touch(exist_ok=True)


def create_one_sample(base: Path) -> None:
    (base / "dir_a").mkdir(parents=True, exist_ok=True)
    (base / "dir_b").mkdir(parents=True, exist_ok=True)

    for i in range(DIR_A_FILES):
        touch(base / "dir_a" / f"a_{i:04d}.txt")
    for i in range(DIR_B_FILES):
        touch(base / "dir_b" / f"b_{i:04d}.txt")
    for i in range(TOP_FILES):
        touch(base / f"file_{i:04d}.txt")


def main() -> int:
    root = Path(os.getenv("ROOT", "./test_fixture"))
    samples = env_int("SAMPLES", 1)
    reset = os.getenv("RESET", "0") == "1"

    if reset and root.exists():
        shutil.rmtree(root)

    root.mkdir(parents=True, exist_ok=True)

    for s in range(samples):
        base = root / f"sample_{s:06d}"
        base.mkdir(parents=True, exist_ok=True)
        create_one_sample(base)

    print(f"created: {root} (samples={samples})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
