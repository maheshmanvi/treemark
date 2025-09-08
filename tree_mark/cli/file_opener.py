# tree_mark/cli/file_opener.py
import os
import sys
import webbrowser
import shutil
from typing import List, Tuple, Optional
from pathlib import Path
from loguru import logger

def list_output_files(outputs_dir: str) -> List[Path]:
    """
    Return a sorted list of Path objects for .md and .json files under outputs_dir.
    Non-recursive (top-level only). If you prefer recursive, change to rglob.
    """
    p = Path(outputs_dir)
    if not p.exists() or not p.is_dir():
        return []
    files = []
    for entry in sorted(p.iterdir()):
        if entry.is_file() and entry.suffix.lower() in (".md", ".json"):
            files.append(entry)
    return files

def _find_chrome_executable() -> Optional[str]:
    """
    Try to detect Chrome executable. Return the name/path for webbrowser.get() if possible.
    Common candidates on Windows: 'chrome', 'chrome.exe', or full path.
    On Linux: 'google-chrome', 'chrome', etc.
    """
    candidates = [
        "chrome",
        "chrome.exe",
        "google-chrome",
        "google-chrome-stable",
        "/usr/bin/google-chrome",
        "/usr/bin/chrome",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for c in candidates:
        # If c is an absolute path, check it directly
        if os.path.isabs(c):
            if os.path.exists(c):
                return c
        else:
            found = shutil.which(c)
            if found:
                return found
    return None

def open_file_in_browser(path: Path) -> Tuple[bool, str]:
    """
    Open a file (Path) in Chrome if possible, otherwise default browser.
    Returns (success, message).
    """
    try:
        if not path.exists():
            return False, f"File not found: {path}"

        uri = path.resolve().as_uri()  # file://... URI works cross-platform for webbrowser

        chrome_exec = _find_chrome_executable()
        if chrome_exec:
            try:
                # Try to register and use Chrome specifically
                # Use a unique name to avoid overriding existing browser entries
                webbrowser.register("local-chrome", None, webbrowser.BackgroundBrowser(chrome_exec))
                opened = webbrowser.get("local-chrome").open(uri)
                if opened:
                    return True, f"Opened in Chrome: {path}"
            except Exception as exc:
                # fall back to default
                logger.debug("Failed to open with Chrome: {}", exc)

        # fallback to default browser
        opened = webbrowser.open(uri)
        if opened:
            return True, f"Opened in default browser: {path}"
        else:
            return False, "webbrowser.open returned False (could not open)."

    except Exception as exc:
        logger.exception("Error opening file in browser: {}", exc)
        return False, f"Exception while trying to open file: {exc}"
