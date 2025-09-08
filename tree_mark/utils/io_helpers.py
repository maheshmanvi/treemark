# tree_mark/utils/io_helpers.py
import os
import re
from typing import Tuple

def ensure_outputs_dir(outputs_dir: str) -> str:
    """Ensure the outputs directory exists and return its absolute path."""
    outputs_dir = os.path.abspath(outputs_dir)
    os.makedirs(outputs_dir, exist_ok=True)
    return outputs_dir

def sanitize_path_for_filename(path: str, max_len: int = 200) -> str:
    """
    Turn an arbitrary path into a readable filename-friendly string.
    Examples:
      'D:\\Projects\\Helpers\\treemark\\tree_mark' -> 'D__Projects__Helpers__treemark__tree_mark'
    Keep it human-readable (not hashed) so user can understand which path produced the file.
    """
    p = os.path.normpath(path)
    # Remove drive colon (e.g. C:) but keep drive letter
    p = p.replace(':', '')
    # Replace separators with double underscore for clarity
    p = p.replace(os.sep, '__')
    # Replace non-alphanumeric chars with underscore
    p = re.sub(r'[^A-Za-z0-9_\\-]+', '_', p)
    # Clamp length to avoid extremely long filenames
    if len(p) > max_len:
        p = p[:max_len]
    return p
