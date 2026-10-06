"""Disk hard-cap helpers for F012 collectors (owner: never risk filling the disk)."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def dir_size_bytes(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                continue
    return total


def free_bytes(path: Path) -> int:
    path.mkdir(parents=True, exist_ok=True)
    return shutil.disk_usage(path).free


def allow_write(
    out_dir: Path,
    *,
    max_dir_bytes: int,
    min_free_bytes: int,
    upcoming_bytes: int = 0,
) -> tuple[bool, str]:
    """Return (ok, reason). Refuse if dir would exceed cap or free space would fall below floor."""
    used = dir_size_bytes(out_dir)
    if used + upcoming_bytes > max_dir_bytes:
        return False, f"dir_cap used={used} upcoming={upcoming_bytes} cap={max_dir_bytes}"
    free = free_bytes(out_dir)
    if free - upcoming_bytes < min_free_bytes:
        return False, f"free_floor free={free} upcoming={upcoming_bytes} floor={min_free_bytes}"
    return True, "ok"
