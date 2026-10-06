from pathlib import Path

from f012_collectors.disk_guard import allow_write, dir_size_bytes


def test_dir_size_and_cap(tmp_path: Path):
    f = tmp_path / "a.bin"
    f.write_bytes(b"x" * 1000)
    assert dir_size_bytes(tmp_path) == 1000
    ok, reason = allow_write(tmp_path, max_dir_bytes=500, min_free_bytes=1, upcoming_bytes=0)
    assert ok is False
    assert "dir_cap" in reason
    ok2, _ = allow_write(tmp_path, max_dir_bytes=5000, min_free_bytes=1, upcoming_bytes=0)
    assert ok2 is True
