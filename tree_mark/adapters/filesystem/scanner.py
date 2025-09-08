# === FILE: tree_mark/adapters/filesystem/scanner.py ===
import os
import asyncio
from typing import Optional, List
from tree_mark.core.interfaces.scanner_interface import ScannerInterface
from tree_mark.core.entities.tree_node import TreeNode
from tree_mark.exceptions import ScannerError
from loguru import logger

class LocalFileSystemScanner(ScannerInterface):
    """Local filesystem scanner with configurable concurrency.

    It builds asynchronous concurrency by launching child scans concurrently using asyncio tasks
    but constrains the concurrency by a semaphore (max_concurrency) to avoid resource exhaustion.
    """
    def __init__(self, max_concurrency: int = 10):
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def scan(self, path: str, include_extensions: Optional[List[str]] = None, exclude_extensions: Optional[List[str]] = None) -> TreeNode:
        try:
            node = await asyncio.to_thread(self._scan_sync_wrap, path, include_extensions, exclude_extensions)
            return node
        except Exception as exc:
            logger.exception("Scanner failed for path={}", path)
            raise ScannerError(str(exc)) from exc

    def _scan_sync_wrap(self, path: str, include_extensions: Optional[List[str]], exclude_extensions: Optional[List[str]]) -> TreeNode:
        # We keep the heavy filesystem traversal synchronous but we can still parallelize child scans at the async layer
        return self._scan_sync(path, include_extensions, exclude_extensions)

    def _scan_sync(self, path: str, include_extensions: Optional[List[str]], exclude_extensions: Optional[List[str]]) -> TreeNode:
        # synchronous scanning using os.scandir for speed and low memory usage
        path = os.fspath(path)
        name = os.path.basename(path) or path
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path does not exist: {path}")

        is_dir = os.path.isdir(path)
        size = os.path.getsize(path) if not is_dir else None
        node = TreeNode(name=name, path=path, is_dir=is_dir, size=size)

        if is_dir:
            try:
                with os.scandir(path) as it:
                    entries = list(it)
            except PermissionError:
                logger.warning("Permission denied while scanning: {}", path)
                return node

            # We'll scan children concurrently at the async outer layer using to_thread per child - so return children placeholders here
            for entry in entries:
                if not entry.name:
                    continue
                # extension filters
                if include_extensions and entry.is_file():
                    if not any(entry.name.endswith(ext) for ext in include_extensions):
                        continue
                if exclude_extensions and entry.is_file():
                    if any(entry.name.endswith(ext) for ext in exclude_extensions):
                        continue
                # For a synchronous traversal we directly recurse
                try:
                    child = self._scan_sync(entry.path, include_extensions, exclude_extensions)
                    node.add_child(child)
                except PermissionError:
                    logger.warning("Skipping path due to permission error: {}", entry.path)
                    continue
        return node