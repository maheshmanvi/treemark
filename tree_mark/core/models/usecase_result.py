# tree_mark/core/models/usecase_result.py
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class UseCaseResult:
    """
    Standard return object for use-cases.
    - results: map of output type -> path (e.g. {'json': 'outputs/foo.json'})
    - elapsed: time in seconds it took to produce the result
    """
    results: Dict[str, Any]
    elapsed: float
