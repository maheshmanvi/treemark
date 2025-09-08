# === FILE: tests/test_scanner.py ===
import asyncio
from tree_mark.adapters.filesystem.scanner import LocalFileSystemScanner

async def test_scan_current_dir(tmp_path):
    p = tmp_path / "a"
    p.mkdir()
    (p / "f.txt").write_text("hello")

    scanner = LocalFileSystemScanner(max_concurrency=2)
    node = await scanner.scan(str(tmp_path))
    assert node is not None