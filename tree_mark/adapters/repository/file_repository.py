# === FILE: tree_mark/adapters/repository/file_repository.py ===
import os
import aiofiles
from typing import Any
from loguru import logger
from tree_mark.exceptions import RepositoryError

async def write_text_file(path: str, content: str, overwrite: bool = True) -> str:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        mode = 'w'
        async with aiofiles.open(path, mode) as f:
            await f.write(content)
        return path
    except Exception as exc:
        logger.exception("Failed to write file: {}", path)
        raise RepositoryError(str(exc)) from exc

async def write_json_file(path: str, data: Any, overwrite: bool = True) -> str:
    import json
    try:
        text = json.dumps(data, ensure_ascii=False, indent=2)
        return await write_text_file(path, text, overwrite)
    except Exception as exc:
        logger.exception("Failed to write json file: {}", path)
        raise RepositoryError(str(exc)) from exc