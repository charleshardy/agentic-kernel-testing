"""
Infrastructure Selection Strategies

This module contains strategy classes for selecting optimal resources.
"""

from infrastructure.strategies.build_server_strategy import BuildServerSelectionStrategy
from infrastructure.strategies.host_strategy import HostSelectionStrategy
from infrastructure.strategies.board_strategy import BoardSelectionStrategy

__all__ = [
    "BuildServerSelectionStrategy",
    "HostSelectionStrategy",
    "BoardSelectionStrategy",
]
