# === FILE: tests/test_scanner.py ===

import asyncio
import pytest
from tree_mark.adapters.filesystem.scanner import LocalFileSystemScanner

@pytest.mark.asyncio
async def test_scan_current_dir(tmp_path):
    p = tmp_path / "a"
    p.mkdir()
    (p / "f.txt").write_text("hello")

    scanner = LocalFileSystemScanner(max_concurrency=2)
    node = await scanner.scan(str(tmp_path))
    assert node is not None


# def test_scan_current_dir(tmp_path):
#     async def _inner():
#         p = tmp_path / "a"
#         p.mkdir()
#         (p / "f.txt").write_text("hello")
#
#         scanner = LocalFileSystemScanner(max_concurrency=2)
#         node = await scanner.scan(str(tmp_path))
#         assert node is not None
#
#     asyncio.run(_inner())
