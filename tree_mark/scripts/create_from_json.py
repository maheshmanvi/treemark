# tree_mark/scripts/create_from_json.py
"""
Recreate filesystem structure from a TreeMark JSON description.

- Supports new JSON format: { "tree": {...}, "flat": [...] }
- Supports legacy JSON with 'path' fields (kept for backward compatibility).
- When flat list exists, prefer it because it's straightforward to map to directories/files.

Note: This script creates empty files for files found in the structure.
"""

import json
import os
import asyncio
from typing import Any, Dict, List
from tree_mark.exceptions import RepositoryError
from tree_mark.adapters.repository.file_repository import write_text_file
from tree_mark.adapters.serializers.json_serializer import deserialize_json_to_tree
from loguru import logger

# OLD implementation (kept for reference):
# async def _create_node(node: dict, dest: str, dry_run: bool = False):
#     path = os.path.join(dest, node['name'])
#     if node['type'] == 'directory':
#         if dry_run:
#             logger.info("Would create dir: {}", path)
#         else:
#             os.makedirs(path, exist_ok=True)
#             logger.info("Created dir: {}", path)
#         if node.get('children'):
#             for child in node['children']:
#                 await _create_node(child, path, dry_run)
#     else:
#         # create empty file
#         if dry_run:
#             logger.info("Would create file: {}", path)
#         else:
#             await write_text_file(path, "")
#             logger.info("Created file: {}", path)

async def _create_from_flat_list(flat: List[str], dest: str, dry_run: bool = False) -> None:
    """
    Create files & directories from a flat list of file paths.
    Each entry is relative (e.g., 'app/service/file.py'). We join with dest to create full paths.
    """
    for rel in flat:
        target = os.path.join(dest, *rel.strip("/").split("/"))
        dirpath = os.path.dirname(target)
        try:
            if dry_run:
                logger.info("Would create directory: {}", dirpath)
                logger.info("Would create file: {}", target)
            else:
                os.makedirs(dirpath, exist_ok=True)
                # create empty file
                await write_text_file(target, "")
                logger.info("Created file: {}", target)
        except Exception as exc:
            logger.exception("Failed to create file for path: {}", target)
            raise RepositoryError(str(exc)) from exc

async def _create_from_tree(node: Dict[str, Any], dest: str, dry_run: bool = False) -> None:
    """
    Create files & directories from the nested tree dict (name/type/children).
    We treat the nested 'name' segments as relative path components.
    """
    name = node.get("name", "")
    node_type = node.get("type", "file")
    current_path = os.path.join(dest, name) if name else dest

    try:
        if node_type == "directory":
            if dry_run:
                logger.info("Would create directory: {}", current_path)
            else:
                os.makedirs(current_path, exist_ok=True)
                logger.info("Created directory: {}", current_path)

            for child in node.get("children", []) or []:
                await _create_from_tree(child, current_path, dry_run)
        else:
            # file
            if dry_run:
                logger.info("Would create file: {}", current_path)
            else:
                # Ensure parent directory exists
                parent = os.path.dirname(current_path)
                os.makedirs(parent, exist_ok=True)
                await write_text_file(current_path, "")
                logger.info("Created file: {}", current_path)
    except Exception as exc:
        logger.exception("Failed to create node: {}", current_path)
        raise RepositoryError(str(exc)) from exc


async def recreate_from_json(json_path: str, dest: str, dry_run: bool = False) -> None:
    """
    Public entrypoint: read json file and recreate structure under dest.
    Handles:
      - combined format { "tree": {...}, "flat": [...] }
      - legacy nested format with 'path' keys
      - flat list (top-level JSON array)
    """
    try:
        with open(json_path, 'r', encoding='utf8') as f:
            data = json.load(f)
    except Exception as exc:
        logger.exception("Failed to read json: {}", json_path)
        raise RepositoryError(str(exc)) from exc

    # If data is a dict and contains flat list -> use that
    if isinstance(data, dict) and "flat" in data:
        flat = data["flat"] or []
        await _create_from_flat_list(flat, dest, dry_run)
        return

    # If top-level is a list -> treat as flat list
    if isinstance(data, list):
        await _create_from_flat_list(data, dest, dry_run)
        return

    # If dict with 'tree'
    if isinstance(data, dict) and "tree" in data:
        tree = data["tree"]
        # Create root inside dest
        await _create_from_tree(tree, dest, dry_run)
        return

    # Otherwise try to interpret legacy node dict with 'path' fields
    # We'll build a helper to recurse using path fields
    async def legacy_create(d: Dict[str, Any], _dest: str, _dry: bool):
        # If node has 'path' - use it relative to _dest root
        p = d.get("path", None)
        if p:
            # make relative path (strip drive / absolute prefix)
            rel = p
            # If absolute, make relative by taking basename chain
            rel = rel.strip("/\\")
            target = os.path.join(_dest, *rel.split(os.sep))
            if d.get("type", "") == "directory":
                if _dry:
                    logger.info("Would create directory: {}", target)
                else:
                    os.makedirs(target, exist_ok=True)
                    logger.info("Created directory: {}", target)
                for child in d.get("children", []) or []:
                    await legacy_create(child, _dest, _dry)
            else:
                if _dry:
                    logger.info("Would create file: {}", target)
                else:
                    parent = os.path.dirname(target)
                    os.makedirs(parent, exist_ok=True)
                    await write_text_file(target, "")
                    logger.info("Created file: {}", target)

    # Fallback: if data is dict, assume legacy structure
    if isinstance(data, dict):
        await legacy_create(data, dest, dry_run)
        return

    # Unknown format
    raise RepositoryError("Unsupported JSON format for recreation.")
