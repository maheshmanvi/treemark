# === FILE: tree_mark/core/interfaces/scanner_interface.py ===
from abc import ABC, abstractmethod
from typing import Optional
from tree_mark.core.entities.tree_node import TreeNode


class ScannerInterface(ABC):
    @abstractmethod
    async def scan(self, path: str, include_extensions: Optional[list[str]] = None, exclude_extensions: Optional[list[str]] = None) -> TreeNode:
        """Scan a path and return a TreeNode representation.
        Implementations must be async-friendly.
        """
        raise NotImplementedError