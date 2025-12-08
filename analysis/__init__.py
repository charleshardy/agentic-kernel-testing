"""Analysis module for code changes, coverage, and failures."""

__version__ = "0.1.0"

from .code_analyzer import CodeAnalyzer, DiffParser, ASTAnalyzer, FileDiff
from .git_integration import GitRepository
from .root_cause_analyzer import (
    RootCauseAnalyzer,
    StackTraceParser,
    ErrorPatternRecognizer,
    FailureSignatureGenerator
)

__all__ = [
    "CodeAnalyzer",
    "DiffParser", 
    "ASTAnalyzer",
    "FileDiff",
    "GitRepository",
    "RootCauseAnalyzer",
    "StackTraceParser",
    "ErrorPatternRecognizer",
    "FailureSignatureGenerator"
]
