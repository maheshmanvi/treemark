# === FILE: tree_mark/core/entities/tree_node.py ===
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TreeNode:
    name: str
    path: str
    is_dir: bool
    size: Optional[int] = None
    children: List["TreeNode"] = field(default_factory=list)


    def add_child(self, child: "TreeNode") -> None:
        self.children.append(child)