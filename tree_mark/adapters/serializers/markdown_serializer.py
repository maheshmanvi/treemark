# === FILE: tree_mark/adapters/serializers/markdown_serializer.py ===
import os
import re
from typing import List
from tree_mark.core.entities.tree_node import TreeNode
from tree_mark.exceptions import SerializationError
from loguru import logger


def node_to_markdown_lines(node: TreeNode, depth: int = 0, keep_extensions: bool = True) -> List[str]:
    try:
        lines: List[str] = []
        indent = '  ' * depth
        prefix = f"{indent}- "
        # Optionally strip extension for file names in Markdown
        display_name = node.name
        if not keep_extensions and not node.is_dir:
            display_name = os.path.splitext(node.name)[0]
        entry = f"{prefix}{display_name}/" if node.is_dir else f"{prefix}{display_name}"
        lines.append(entry)
        if node.children:
            for child in node.children:
                lines.extend(node_to_markdown_lines(child, depth + 1, keep_extensions))
        return lines
    except Exception as exc:
        logger.exception("Markdown conversion error")
        raise SerializationError(str(exc)) from exc

async def serialize_to_markdown(node: TreeNode, keep_extensions: bool = True) -> str:
    """Serialize tree to Markdown. Set keep_extensions=False to remove extensions from displayed file names."""
    lines = node_to_markdown_lines(node, keep_extensions=keep_extensions)
    return "\n".join(lines)

# ------------------------------------------------------------------
# Markdown -> TreeNode parser

def parse_markdown_to_tree(md_text: str) -> TreeNode:
    """
    Parse the simple nested markdown format we produce:
      - root/
        - child/
          - file.txt
    Assumes indentation is 2 spaces per level as produced elsewhere.
    """
    lines = [ln for ln in md_text.splitlines() if ln.strip()]
    if not lines:
        return TreeNode(name="empty", path="", is_dir=True)

    # We will use a stack of (depth, node)
    root_line = lines[0]
    # extract the root name
    m = re.match(r'\s*- (.+)', root_line)
    root_name = m.group(1).rstrip('/') if m else root_line.strip().rstrip('/')
    root = TreeNode(name=root_name, path=root_name, is_dir=root_line.strip().endswith('/'))
    stack = [(0, root)]

    for line in lines[1:]:
        # count leading spaces
        leading = len(line) - len(line.lstrip(' '))
        depth = leading // 2  # we used '  ' per level
        # extract name (strip '- ' and trailing '/')
        name_part = line.strip().lstrip('- ').rstrip('/')
        is_dir = line.strip().endswith('/')
        node = TreeNode(name=name_part, path=name_part, is_dir=is_dir)
        # find parent
        while stack and stack[-1][0] >= depth:
            stack.pop()
        parent_depth, parent_node = stack[-1]
        parent_node.add_child(node)
        stack.append((depth, node))

    return root
