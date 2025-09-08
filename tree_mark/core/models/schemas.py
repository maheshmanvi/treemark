# === FILE: tree_mark/core/models/schemas.py ===
from __future__ import annotations
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class NodeType(str, Enum):
    DIRECTORY = "directory"
    FILE = "file"
    ARCHIVE = "archive"


class OutputFormat(str, Enum):
    JSON = "json"
    MARKDOWN = "markdown"
    BOTH = "both"


class NodeSchema(BaseModel):
    name: str
    path: str
    type: NodeType
    size: Optional[int] = None
    children: Optional[List["NodeSchema"]] = None

    class Config:
        from_attributes = True


class ExportNodeSchema(BaseModel):
    """
    Schema for the exported JSON tree format used by TreeMark:
    nodes contain only: name, type, children (no path, no size).
    """
    name: str
    type: NodeType
    children: Optional[List["ExportNodeSchema"]] = None

# NodeSchema.update_forward_refs() # Deprecated in Pydantic v2
NodeSchema.model_rebuild()