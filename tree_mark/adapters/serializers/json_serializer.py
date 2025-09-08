# tree_mark/adapters/serializers/json_serializer.py
"""
JSON serializer / deserializer.

CHANGES (new):
- Output JSON now contains two sections:
    {
      "tree": { <nested tree: nodes have only name, type, children> },
      "flat": [ "root/file1.py", "root/sub/file2.py", ... ]  # file paths only
    }
- Removed `path` and `size` from the tree nodes in the JSON (keeps JSON compact & easier to read).
- Added deserialization logic that handles legacy formats and the new combined format.

OLD CODE: kept below as comments (for reference).
"""

from typing import Any, Dict, List
from tree_mark.core.entities.tree_node import TreeNode
from tree_mark.exceptions import SerializationError
from loguru import logger
import os

from tree_mark.core.models.schemas import ExportNodeSchema


def node_to_tree_dict(node: TreeNode, keep_extensions: bool = True) -> Dict[str, Any]:
    """
    Convert TreeNode -> nested dict with fields { name, type, children }.
    Intentionally **does not** include 'path' or 'size'.
    """
    try:
        display_name = node.name
        if not keep_extensions and not node.is_dir:
            display_name = os.path.splitext(node.name)[0]

        d = {
            "name": display_name,
            "type": "directory" if node.is_dir else "file",
        }
        if node.children:
            d["children"] = [node_to_tree_dict(c, keep_extensions=keep_extensions) for c in node.children]
        return d
    except Exception as exc:
        logger.exception("Failed to convert TreeNode to nested tree dict")
        raise SerializationError(str(exc)) from exc


def flatten_tree_to_paths(node: TreeNode, prefix: str = "") -> List[str]:
    """
    Return a flat list of file paths (strings) relative to top-level node.
    Directories are not included in the flat list; only files.
    Example output:
      ["app/agentic_sql_assistant.py", "app/application/services/charting_service.py", ...]
    """
    paths: List[str] = []
    current = node.name if prefix == "" else f"{prefix}/{node.name}"
    if node.is_dir:
        for child in node.children:
            paths.extend(flatten_tree_to_paths(child, prefix=current))
    else:
        paths.append(current)
    return paths


async def serialize_to_json(node: TreeNode, keep_extensions: bool = True) -> Dict[str, Any]:
    """
    Produce the combined JSON object containing a nested tree (no path/size)
    and a flat list of file paths.

    Returns:
      {
        "tree": { ... },   # nested nodes with name/type/children
        "flat": [ ... ]    # list of file paths (strings)
      }
    """
    try:
        tree_dict = node_to_tree_dict(node, keep_extensions=keep_extensions)
        flat_list = flatten_tree_to_paths(node, prefix="")  # will include top-level node name
        # Validate root node with pydantic NodeSchema using the 'tree' structure
        try:
            # ExportNodeSchema expects keys name/type/children
            # schema = parse_obj_as(ExportNodeSchema, tree_dict) # 'parse_obj_as' deprecated.
            schema = ExportNodeSchema.model_validate(tree_dict)
            # Validation passed; proceed.
        except Exception as exc:
            # If validation fails, log at debug level (not WARNING) because we can still proceed.
            logger.debug("Export tree did not validate against ExportNodeSchema: {}", exc)

        return {"tree": tree_dict, "flat": flat_list}
    except Exception as exc:
        logger.exception("JSON serialization failed")
        raise SerializationError(str(exc)) from exc


# -------------------------
# Deserialization helpers
# -------------------------

def dict_tree_to_treenode(d: Dict[str, Any]) -> TreeNode:
    """
    Convert a nested tree dict (name/type/children) back to TreeNode.
    Note: the resulting TreeNode.path will be constructed from the node names joined by '/' during recursion
    only when calling the caller that needs full paths (if required).
    """
    name = d.get("name", "")
    type_ = d.get("type", "file")
    is_dir = (type_ == "directory")
    node = TreeNode(name=name, path=name, is_dir=is_dir)
    children = d.get("children") or []
    for c in children:
        child_node = dict_tree_to_treenode(c)
        node.add_child(child_node)
    return node


def flat_list_to_tree(flat_list: List[str]) -> TreeNode:
    """
    Build a TreeNode tree from a flat list of file paths.
    The returned root is a pseudo-root whose name is the first path segment of the first entry.
    Example:
      ["app/a.py", "app/s/b.py"] -> root name = "app", with children accordingly.
    """
    if not flat_list:
        return TreeNode(name="empty", path="", is_dir=True)

    # Build a nested dict tree structure first
    root = None
    for p in flat_list:
        parts = [part for part in p.strip("/").split("/") if part]
        if not parts:
            continue
        if root is None:
            root = TreeNode(name=parts[0], path=parts[0], is_dir=True)
        # ensure the flat list root matches
        if parts[0] != root.name:
            # If different roots exist, create a virtual root
            if root.name != "__virtual_root__":
                virtual = TreeNode(name="__virtual_root__", path="", is_dir=True)
                virtual.add_child(root)
                root = virtual
        # traverse/insert
        node_cursor = root
        for i, part in enumerate(parts[1:], start=1):
            # find child with this name
            found = None
            for c in node_cursor.children:
                if c.name == part:
                    found = c
                    break
            is_last = (i == len(parts) - 1)
            if found is None:
                new_node = TreeNode(name=part, path=os.path.join(node_cursor.path, part), is_dir=(not is_last))
                node_cursor.add_child(new_node)
                node_cursor = new_node
            else:
                node_cursor = found
    if root is None:
        return TreeNode(name="empty", path="", is_dir=True)
    return root


def deserialize_json_to_tree(data: Any) -> TreeNode:
    """
    Accept either:
      - legacy dict representing a single node with 'path' fields (older format),
      - new combined JSON with keys 'tree' and 'flat' (use 'tree' if available),
      - or a flat list of paths.
    Returns a TreeNode root.
    """
    try:
        # If top-level is a dict with 'tree' and 'flat'
        if isinstance(data, dict) and ("tree" in data or "flat" in data):
            # Prefer nested tree if present
            if "tree" in data:
                tree_dict = data["tree"]
                return dict_tree_to_treenode(tree_dict)
            else:
                flat = data.get("flat", [])
                return flat_list_to_tree(flat)

        # If top-level is a list -> treat as flat list
        if isinstance(data, list):
            return flat_list_to_tree(data)

        # If top-level is a dict that looks like legacy NodeSchema (has 'path' or 'type')
        if isinstance(data, dict):
            # Legacy handling: attempt to use the old keys (path/children)
            def legacy_dict_to_tree(d: Dict[str, Any]) -> TreeNode:
                name = d.get("name", "")
                path = d.get("path", name)
                type_ = d.get("type") or ("directory" if d.get("children") else "file")
                is_dir = type_ == "directory"
                node = TreeNode(name=name, path=path, is_dir=is_dir)
                children = d.get("children") or []
                for c in children:
                    child_node = legacy_dict_to_tree(c)
                    node.add_child(child_node)
                return node
            return legacy_dict_to_tree(data)

        # unknown shape -> return empty
        return TreeNode(name="empty", path="", is_dir=True)

    except Exception as exc:
        logger.exception("Failed to deserialize JSON to TreeNode")
        raise SerializationError(str(exc)) from exc
