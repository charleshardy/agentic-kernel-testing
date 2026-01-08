"""
Build Server Selection Strategy

Implements algorithms for selecting optimal build servers.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from infrastructure.models.build_server import (
    BuildServer,
    BuildServerStatus,
    BuildRequirements,
    BuildServerSelectionResult,
)

logger = logging.getLogger(__name__)


@dataclass
class BuildResourceReservation:
    """Resource reservation for a build."""
    id: str
    server_id: str
    cpu_cores: int
    memory_mb: int
    storage_gb: int
    created_at: datetime
    expires_at: Optional[datetime] = None


class BuildServerSelectionStrategy:
    """
    Strategy for selecting optimal build servers.
    
    Uses scoring algorithm based on architecture support, current load,
    and estimated build time.
    """

    def __init__(
        self,
        servers: Dict[str, BuildServer],
        utilization_weight: float = 0.4,
        queue_weight: float = 0.3,
        capacity_weight: float = 0.3
    ):
        """
        Initialize Build Server Selection Strategy.
        
        Args:
            servers: Dictionary of available build servers
            utilization_weight: Weight for utilization in scoring
            queue_weight: Weight for queue depth in scoring
            capacity_weight: Weight for available capacity in scoring
        """
        self._servers = servers
        self.utilization_weight = utilization_weight
        self.queue_weight = queue_weight
        self.capacity_weight = capacity_weight
        
        # Track reservations
        self._reservations: Dict[str, BuildResourceReservation] = {}
        self._reservation_lock = asyncio.Lock()

    async def select_server(
        self,
        requirements: BuildRequirements
    ) -> BuildServerSelectionResult:
        """
        Select the best build server for given requirements.
        
        Args:
            requirements: Build requirements
            
        Returns:
            BuildServerSelectionResult with selected server
        """
        # Check for preferred server first
        if requirements.preferred_server_id:
            server = self._servers.get(requirements.preferred_server_id)
            if server and self._meets_requirements(server, requirements):
                return BuildServerSelectionResult(
                    success=True,
                    server=server
                )
        
        # Get compatible servers
        compatible = await self.get_compatible_servers(requirements)
        
        if not compatible:
            return BuildServerSelectionResult(
                success=False,
                error_message="No compatible build servers available",
                estimated_wait_time=self._estimate_wait_time(requirements)
            )
        
        # Score and sort servers
        scored_servers = []
        for server in compatible:
            score = await self.calculate_server_score(server, requirements)
            scored_servers.append((server, score))
        
        scored_servers.sort(key=lambda x: x[1], reverse=True)
        
        # Select best server
        best_server = scored_servers[0][0]
        alternatives = [s for s, _ in scored_servers[1:4]]  # Top 3 alternatives
        
        return BuildServerSelectionResult(
            success=True,
            server=best_server,
            alternative_servers=alternatives
        )

    async def get_compatible_servers(
        self,
        requirements: BuildRequirements
    ) -> List[BuildServer]:
        """
        Get all servers that meet the requirements.
        
        Args:
            requirements: Build requirements
            
        Returns:
            List of compatible BuildServer objects
        """
        compatible = []
        
        for server in self._servers.values():
            if self._meets_requirements(server, requirements):
                compatible.append(server)
        
        return compatible

    async def calculate_server_score(
        self,
        server: BuildServer,
        requirements: BuildRequirements
    ) -> float:
        """
        Calculate a score for a server based on requirements.
        
        Higher score = better choice.
        
        Args:
            server: Build server to score
            requirements: Build requirements
            
        Returns:
            Score between 0 and 1
        """
        if not self._meets_requirements(server, requirements):
            return 0.0
        
        # Utilization score (lower is better)
        utilization = server.current_utilization
        avg_utilization = (
            utilization.cpu_percent +
            utilization.memory_percent +
            utilization.storage_percent
        ) / 3
        utilization_score = 1.0 - (avg_utilization / 100.0)
        
        # Queue score (lower queue is better)
        max_queue = server.max_concurrent_builds * 2  # Assume max queue is 2x concurrent
        queue_score = 1.0 - min(server.queue_depth / max_queue, 1.0)
        
        # Capacity score (more available capacity is better)
        capacity = server.get_capacity()
        cpu_ratio = min(capacity.available_cpu_cores / requirements.min_cpu_cores, 2.0) / 2.0
        mem_ratio = min(capacity.available_memory_mb / requirements.min_memory_mb, 2.0) / 2.0
        storage_ratio = min(capacity.available_storage_gb / requirements.min_storage_gb, 2.0) / 2.0
        capacity_score = (cpu_ratio + mem_ratio + storage_ratio) / 3
        
        # Weighted total
        total_score = (
            self.utilization_weight * utilization_score +
            self.queue_weight * queue_score +
            self.capacity_weight * capacity_score
        )
        
        return total_score

    async def estimate_build_time(
        self,
        server: BuildServer,
        requirements: BuildRequirements
    ) -> int:
        """
        Estimate build time on a server.
        
        Args:
            server: Build server
            requirements: Build requirements
            
        Returns:
            Estimated time in seconds
        """
        # Base estimate: 10 minutes for a typical kernel build
        base_time = 600
        
        # Adjust based on CPU cores
        cpu_factor = max(1, requirements.min_cpu_cores) / max(1, server.total_cpu_cores)
        
        # Adjust based on current load
        load_factor = 1.0 + (server.current_utilization.cpu_percent / 100.0)
        
        # Adjust based on queue
        queue_factor = 1.0 + (server.queue_depth * 0.5)
        
        estimated = int(base_time * cpu_factor * load_factor * queue_factor)
        
        return estimated

    async def reserve_capacity(
        self,
        server_id: str,
        resources: BuildResourceReservation
    ) -> Optional[str]:
        """
        Reserve capacity on a server.
        
        Args:
            server_id: Server identifier
            resources: Resources to reserve
            
        Returns:
            Reservation ID if successful
        """
        async with self._reservation_lock:
            server = self._servers.get(server_id)
            if not server:
                return None
            
            # Check if server can accommodate
            capacity = server.get_capacity()
            if not capacity.meets_requirements(
                resources.cpu_cores,
                resources.memory_mb,
                resources.storage_gb
            ):
                return None
            
            # Create reservation
            reservation_id = str(uuid.uuid4())
            resources.id = reservation_id
            resources.server_id = server_id
            resources.created_at = datetime.now(timezone.utc)
            
            self._reservations[reservation_id] = resources
            
            # Update server queue
            server.queue_depth += 1
            
            logger.info(f"Reserved capacity on server {server_id}: {reservation_id}")
            return reservation_id

    async def release_capacity(
        self,
        reservation_id: str
    ) -> bool:
        """
        Release a capacity reservation.
        
        Args:
            reservation_id: Reservation identifier
            
        Returns:
            True if successful
        """
        async with self._reservation_lock:
            reservation = self._reservations.get(reservation_id)
            if not reservation:
                return False
            
            server = self._servers.get(reservation.server_id)
            if server:
                server.queue_depth = max(0, server.queue_depth - 1)
            
            del self._reservations[reservation_id]
            
            logger.info(f"Released reservation: {reservation_id}")
            return True

    def _meets_requirements(
        self,
        server: BuildServer,
        requirements: BuildRequirements
    ) -> bool:
        """Check if a server meets the requirements."""
        # Must be online and not in maintenance
        if server.status != BuildServerStatus.ONLINE:
            return False
        if server.maintenance_mode:
            return False
        
        # Must have toolchain for target architecture
        if not server.has_toolchain_for(requirements.target_architecture):
            return False
        
        # Check specific toolchain if required
        if requirements.required_toolchain:
            has_toolchain = any(
                tc.name == requirements.required_toolchain and tc.available
                for tc in server.toolchains
            )
            if not has_toolchain:
                return False
        
        # Check capacity
        capacity = server.get_capacity()
        if not capacity.meets_requirements(
            requirements.min_cpu_cores,
            requirements.min_memory_mb,
            requirements.min_storage_gb
        ):
            return False
        
        # Check group if specified
        if requirements.group_id and server.group_id != requirements.group_id:
            return False
        
        # Check labels if specified
        if requirements.required_labels:
            for key, value in requirements.required_labels.items():
                if server.labels.get(key) != value:
                    return False
        
        return True

    def _estimate_wait_time(self, requirements: BuildRequirements) -> int:
        """Estimate wait time when no servers are available."""
        # Find servers that could become available
        potential_servers = []
        for server in self._servers.values():
            if server.has_toolchain_for(requirements.target_architecture):
                potential_servers.append(server)
        
        if not potential_servers:
            return -1  # No servers can handle this architecture
        
        # Estimate based on average queue depth
        avg_queue = sum(s.queue_depth for s in potential_servers) / len(potential_servers)
        estimated_per_build = 600  # 10 minutes per build
        
        return int(avg_queue * estimated_per_build)
