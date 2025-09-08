# === FILE: tree_mark/adapters/filesystem/archive_scanner.py ===
import zipfile
import os
from io import BytesIO
from typing import Optional, List
import asyncio
from tree_mark.core.interfaces.scanner_interface import ScannerInterface
from tree_mark.core.entities.tree_node import TreeNode
from tree_mark.exceptions import ScannerError
from loguru import logger

class ZipArchiveScanner(ScannerInterface):
    """Scans contents of a zip archive and builds a TreeNode representation.

    This scanner treats the ZIP file as a top-level archive node with children matching the zip structure.
    """
    async def scan(self, path: str, include_extensions: Optional[List[str]] = None, exclude_extensions: Optional[List[str]] = None) -> TreeNode:
        try:
            return await asyncio.to_thread(self._scan_sync, path, include_extensions, exclude_extensions)
        except Exception as exc:
            logger.exception("Zip scanner failed for path={}", path)
            raise ScannerError(str(exc)) from exc

    def _scan_sync(self, path: str, include_extensions: Optional[List[str]], exclude_extensions: Optional[List[str]]) -> TreeNode:
        path = os.fspath(path)
        if not zipfile.is_zipfile(path):
            raise FileNotFoundError(f"Not a zip archive: {path}")
        name = os.path.basename(path)
        root = TreeNode(name=name, path=path, is_dir=True)

        with zipfile.ZipFile(path, 'r') as zf:
            # Build a directory tree from zip namelist
            nodes = {"": root}
            for info in zf.infolist():
                parts = info.filename.rstrip('/').split('/')
                # skip top-level empty
                curr_path = ''
                for i, part in enumerate(parts):
                    parent_key = curr_path
                    curr_path = f"{curr_path}/{part}" if curr_path else part
                    if curr_path not in nodes:
                        is_dir = (i < len(parts)-1) or info.is_dir()
                        node = TreeNode(name=part, path=curr_path, is_dir=is_dir, size=(info.file_size if not is_dir else None))
                        nodes[curr_path] = node
                        nodes[parent_key].add_child(node)
            return root