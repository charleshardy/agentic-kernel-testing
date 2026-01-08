"""
Board Selection Strategy

Implements algorithms for selecting optimal physical test boards.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from infrastructure.models.board import (
    Board,
    BoardStatus,
    BoardRequirements,
    BoardSelectionResult,
    HealthLevel,
)

logger = logging.getLogger(__name__)


@dataclass
class BoardReservation:
    """Reservation for a board."""
    id: str
    board_id: str
    test_id: str
    created_at: datetime
    expires_at: Optional[datetime] = None


class BoardSelectionStrategy:
    """
    Strategy for selecting optimal physical test boards.
    
    Uses filtering by architecture, board type, and peripherals,
    with scoring based on health and availability.
    """

    def __init__(
        self,
        boards: Dict[str, Board],
        health_weight: float = 0.4,
        availability_weight: float = 0.35,
        firmware_weight: float = 0.25
    ):
        """
        Initialize Board Selection Strategy.
        
        Args:
            boards: Dictionary of available boards
            health_weight: Weight for health in scoring
            availability_weight: Weight for availability in scoring
            firmware_weight: Weight for firmware match in scoring
        """
        self._boards = boards
        self.health_weight = health_weight
        self.availability_weight = availability_weight
        self.firmware_weight = firmware_weight
        
        # Track reservations
        self._reservations: Dict[str, BoardReservation] = {}
        self._reservation_lock = asyncio.Lock()

    async def select_board(
        self,
        requirements: BoardRequirements
    ) -> BoardSelectionResult:
        """
        Select the best board for given requirements.
        
        Args:
            requirements: Board requirements
            
        Returns:
            BoardSelectionResult with selected board
        """
        # Check for preferred board first
        if requirements.preferred_board_id:
            board = self._boards.get(requirements.preferred_board_id)
            if board and self._meets_requirements(board, requirements):
                requires_flashing = self._requires_flashing(board, requirements)
                return BoardSelectionResult(
                    success=True,
                    board=board,
                    requires_flashing=requires_flashing
                )
        
        # Get compatible boards
        compatible = await self.get_compatible_boards(requirements)
        
        if not compatible:
            return BoardSelectionResult(
                success=False,
                error_message="No compatible boards available",
                estimated_wait_time=self._estimate_wait_time(requirements)
            )
        
        # Score and sort boards
        scored_boards = []
        for board in compatible:
            score = await self.calculate_board_score(board, requirements)
            scored_boards.append((board, score))
        
        scored_boards.sort(key=lambda x: x[1], reverse=True)
        
        # Select best board
        best_board = scored_boards[0][0]
        alternatives = [b for b, _ in scored_boards[1:4]]  # Top 3 alternatives
        requires_flashing = self._requires_flashing(best_board, requirements)
        
        return BoardSelectionResult(
            success=True,
            board=best_board,
            alternative_boards=alternatives,
            requires_flashing=requires_flashing
        )

    async def get_compatible_boards(
        self,
        requirements: BoardRequirements
    ) -> List[Board]:
        """
        Get all boards that meet the requirements.
        
        Args:
            requirements: Board requirements
            
        Returns:
            List of compatible Board objects
        """
        compatible = []
        
        for board in self._boards.values():
            if self._meets_requirements(board, requirements):
                compatible.append(board)
        
        return compatible

    async def calculate_board_score(
        self,
        board: Board,
        requirements: BoardRequirements
    ) -> float:
        """
        Calculate a score for a board based on requirements.
        
        Higher score = better choice.
        
        Args:
            board: Board to score
            requirements: Board requirements
            
        Returns:
            Score between 0 and 1
        """
        if not self._meets_requirements(board, requirements):
            return 0.0
        
        # Health score
        health_score = self._calculate_health_score(board)
        
        # Availability score (available is better than unknown)
        availability_score = 1.0 if board.status == BoardStatus.AVAILABLE else 0.5
        
        # Firmware match score
        firmware_score = 1.0
        if requirements.firmware_version:
            if board.current_firmware_version == requirements.firmware_version:
                firmware_score = 1.0  # Perfect match
            else:
                firmware_score = 0.5  # Will need flashing
        
        # Weighted total
        total_score = (
            self.health_weight * health_score +
            self.availability_weight * availability_score +
            self.firmware_weight * firmware_score
        )
        
        return min(total_score, 1.0)

    async def reserve_board(
        self,
        board_id: str,
        test_id: str
    ) -> Optional[str]:
        """
        Reserve a board for a test.
        
        Args:
            board_id: Board identifier
            test_id: Test identifier
            
        Returns:
            Reservation ID if successful
        """
        async with self._reservation_lock:
            board = self._boards.get(board_id)
            if not board:
                return None
            
            # Check if board can be allocated
            if not board.can_be_allocated():
                return None
            
            # Check if already reserved
            for reservation in self._reservations.values():
                if reservation.board_id == board_id:
                    return None
            
            # Create reservation
            reservation_id = str(uuid.uuid4())
            reservation = BoardReservation(
                id=reservation_id,
                board_id=board_id,
                test_id=test_id,
                created_at=datetime.now(timezone.utc)
            )
            
            self._reservations[reservation_id] = reservation
            
            # Update board status
            board.status = BoardStatus.IN_USE
            board.assigned_test_id = test_id
            
            logger.info(f"Reserved board {board_id} for test {test_id}: {reservation_id}")
            return reservation_id

    async def release_board(
        self,
        board_id: str
    ) -> bool:
        """
        Release a board reservation.
        
        Args:
            board_id: Board identifier
            
        Returns:
            True if successful
        """
        async with self._reservation_lock:
            board = self._boards.get(board_id)
            if not board:
                return False
            
            # Find and remove reservation
            reservation_to_remove = None
            for res_id, reservation in self._reservations.items():
                if reservation.board_id == board_id:
                    reservation_to_remove = res_id
                    break
            
            if reservation_to_remove:
                del self._reservations[reservation_to_remove]
            
            # Update board status
            if board.health.is_healthy():
                board.status = BoardStatus.AVAILABLE
            else:
                board.status = BoardStatus.OFFLINE
            board.assigned_test_id = None
            
            logger.info(f"Released board {board_id}")
            return True

    def _meets_requirements(
        self,
        board: Board,
        requirements: BoardRequirements
    ) -> bool:
        """Check if a board meets the requirements."""
        # Must not be in maintenance
        if board.maintenance_mode:
            return False
        
        # Must be available or unknown status (not offline, flashing, etc.)
        if board.status not in (BoardStatus.AVAILABLE, BoardStatus.UNKNOWN):
            return False
        
        # Must support the architecture
        if not board.supports_architecture(requirements.architecture):
            return False
        
        # Must match board type if specified
        if requirements.board_types and not board.matches_type(requirements.board_types):
            return False
        
        # Must have required peripherals
        if requirements.required_peripherals:
            if not board.has_peripherals(requirements.required_peripherals):
                return False
        
        # Check group if specified
        if requirements.group_id and board.group_id != requirements.group_id:
            return False
        
        # Check labels if specified
        if requirements.required_labels:
            for key, value in requirements.required_labels.items():
                if board.labels.get(key) != value:
                    return False
        
        return True

    def _calculate_health_score(self, board: Board) -> float:
        """Calculate health score for a board."""
        health = board.health
        
        # Connectivity is most important
        if health.connectivity == HealthLevel.HEALTHY:
            base_score = 1.0
        elif health.connectivity == HealthLevel.DEGRADED:
            base_score = 0.5
        else:
            base_score = 0.0
        
        # Adjust for temperature if available
        if health.temperature_celsius is not None:
            if health.temperature_celsius < 60:
                temp_factor = 1.0
            elif health.temperature_celsius < 80:
                temp_factor = 0.8
            else:
                temp_factor = 0.5
            base_score *= temp_factor
        
        # Adjust for storage if available
        if health.storage_percent is not None:
            if health.storage_percent < 70:
                storage_factor = 1.0
            elif health.storage_percent < 90:
                storage_factor = 0.8
            else:
                storage_factor = 0.5
            base_score *= storage_factor
        
        return base_score

    def _requires_flashing(
        self,
        board: Board,
        requirements: BoardRequirements
    ) -> bool:
        """Check if board requires firmware flashing."""
        if not requirements.firmware_version:
            return False
        
        return board.current_firmware_version != requirements.firmware_version

    def _estimate_wait_time(self, requirements: BoardRequirements) -> int:
        """Estimate wait time when no boards are available."""
        # Find boards that could become available
        potential_boards = []
        for board in self._boards.values():
            if board.supports_architecture(requirements.architecture):
                if requirements.board_types:
                    if board.matches_type(requirements.board_types):
                        potential_boards.append(board)
                else:
                    potential_boards.append(board)
        
        if not potential_boards:
            return -1  # No boards can handle this architecture/type
        
        # Count boards in use
        in_use = sum(1 for b in potential_boards if b.status == BoardStatus.IN_USE)
        
        if in_use == 0:
            return -1  # No boards in use, issue is something else
        
        # Estimate based on typical test duration
        estimated_test_duration = 1800  # 30 minutes average test
        
        return int(estimated_test_duration / max(in_use, 1))
