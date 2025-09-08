# === FILE: tree_mark/exceptions.py ===
class TreeMarkError(Exception):
    """Base class for TreeMark errors."""


class ScannerError(TreeMarkError):
    """Raised when scanning fails."""


class SerializationError(TreeMarkError):
    """Raised during serialization failures."""


class RepositoryError(TreeMarkError):
    """Raised when writing output fails."""