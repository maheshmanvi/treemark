# === FILE: tree_mark/factory/scanner_factory.py ===
from typing import Literal
from tree_mark.adapters.filesystem.scanner import LocalFileSystemScanner
from tree_mark.adapters.filesystem.archive_scanner import ZipArchiveScanner
from tree_mark.core.interfaces.scanner_interface import ScannerInterface
import os

class ScannerFactory:
    @staticmethod
    def get_scanner(path: str, kind: Literal['auto','local','zip'] = 'auto', max_concurrency: int = 10) -> ScannerInterface:
        """Return appropriate scanner for the path.
        - 'auto' will inspect the path and choose ZipArchiveScanner for .zip or LocalFileSystemScanner otherwise.
        - 'local' forces local filesystem scanner.
        - 'zip' forces zip scanner.
        """
        if kind == 'auto':
            if os.path.isfile(path) and path.lower().endswith('.zip'):
                return ZipArchiveScanner()
            return LocalFileSystemScanner(max_concurrency=max_concurrency)
        if kind == 'local':
            return LocalFileSystemScanner(max_concurrency=max_concurrency)
        if kind == 'zip':
            return ZipArchiveScanner()
        raise ValueError(f"Unknown scanner kind: {kind}")