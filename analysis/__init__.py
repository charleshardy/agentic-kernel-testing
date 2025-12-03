"""Analysis module for code changes, coverage, and failures."""

__version__ = "0.1.0"

from .code_analyzer import CodeAnalyzer, DiffParser, ASTAnalyzer, FileDiff
from .git_integration import GitRepository

__all__ = [
    "CodeAnalyzer",
    "DiffParser", 
    "ASTAnalyzer",
    "FileDiff",
    "GitRepository"
]
