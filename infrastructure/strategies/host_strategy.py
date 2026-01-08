"""
Host Selection Strategy

Implements algorithms for selecting optimal QEMU hosts for VM allocation.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from infrastructure.models.host import (
    Host,
    HostStatus,
    HostCapacity,
    VMRequirements,
    HostSelectionResult,
)

logger = logging.getLogger(__name__)


@dataclass
class ResourceReservation:
    """Resource reservation for a VM."""
    id: str
    host_id: str
    cpu_cores: int
    memory_mb: int
    storage_gb: int
    created_at: datetime
    expires_at: Optional[datetime] = None


class HostSelectionStrategy:
    """
    Strategy for selecting optimal QEMU hosts.
    
    Uses scoring algorithm based on CPU, memory, architecture,
    and KVM support.
    """

    def __init__(
        self,
        hosts: Dict[str, Host],
        utilization_weight: float = 0.4,
        capacity_weight: float = 0.35,
        vm_count_weight: float = 0.25
    ):
        """
        Initialize Host Selection Strategy.
        
        Args:
            hosts: Dictionary of available hosts
            utilization_weight: Weight for utilization in scoring
            capacity_weight: Weight for available capacity in scoring
            vm_count_weight: Weight for VM count in scoring
        """
        self._hosts = hosts
        self.utilization_weight = utilization_weight
        self.capacity_weight = capacity_weight
        self.vm_count_weight = vm_count_weight
        
        # Track reservations
        self._reservations: Dict[str, ResourceReservation] = {}
        self._reservation_lock = asyncio.Lock()

    async def select_host(
        self,
        requirements: VMRequirements
    ) -> HostSelectionResult:
        """
        Select the best host for given VM requirements.
        
        Args:
            requirements: VM requirements
            
        Returns:
            HostSelectionResult with selected host
        """
        # Check for preferred host first
        if requirements.preferred_host_id:
            host = self._hosts.get(requirements.preferred_host_id)
            if host and self._meets_requirements(host, requirements):
                return HostSelectionResult(
                    success=True,
                    host=host
                )
        
        # Get compatible hosts
        compatible = await self.get_compatible_hosts(requirements)
        
        if not compatible:
            return HostSelectionResult(
                success=False,
                error_message="No compatible hosts available",
                estimated_wait_time=self._estimate_wait_time(requirements)
            )
        
        # Score and sort hosts
        scored_hosts = []
        for host in compatible:
            score = await self.calculate_host_score(host, requirements)
            scored_hosts.append((host, score))
        
        scored_hosts.sort(key=lambda x: x[1], reverse=True)
        
        # Select best host
        best_host = scored_hosts[0][0]
        alternatives = [h for h, _ in scored_hosts[1:4]]  # Top 3 alternatives
        
        return HostSelectionResult(
            success=True,
            host=best_host,
            alternative_hosts=alternatives
        )

    async def get_compatible_hosts(
        self,
        requirements: VMRequirements
    ) -> List[Host]:
        """
        Get all hosts that meet the requirements.
        
        Args:
            requirements: VM requirements
            
        Returns:
            List of compatible Host objects
        """
        compatible = []
        
        for host in self._hosts.values():
            if self._meets_requirements(host, requirements):
                compatible.append(host)
        
        return compatible

    async def calculate_host_score(
        self,
        host: Host,
        requirements: VMRequirements
    ) -> float:
        """
        Calculate a score for a host based on requirements.
        
        Higher score = better choice.
        
        Args:
            host: Host to score
            requirements: VM requirements
            
        Returns:
            Score between 0 and 1
        """
        if not self._meets_requirements(host, requirements):
            return 0.0
        
        # Utilization score (lower is better)
        utilization = host.current_utilization
        avg_utilization = (
            utilization.cpu_percent +
            utilization.memory_percent +
            utilization.storage_percent
        ) / 3
        utilization_score = 1.0 - (avg_utilization / 100.0)
        
        # VM count score (fewer VMs is better)
        vm_ratio = host.running_vm_count / max(host.max_vms, 1)
        vm_count_score = 1.0 - vm_ratio
        
        # Capacity score (more available capacity is better)
        capacity = host.get_capacity()
        cpu_ratio = min(capacity.available_cpu_cores / requirements.min_cpu_cores, 2.0) / 2.0
        mem_ratio = min(capacity.available_memory_mb / requirements.min_memory_mb, 2.0) / 2.0
        storage_ratio = min(capacity.available_storage_gb / requirements.min_storage_gb, 2.0) / 2.0
        capacity_score = (cpu_ratio + mem_ratio + storage_ratio) / 3
        
        # Bonus for KVM support if required
        kvm_bonus = 0.0
        if requirements.require_kvm and host.kvm_enabled:
            kvm_bonus = 0.1
        
        # Weighted total
        total_score = (
            self.utilization_weight * utilization_score +
            self.capacity_weight * capacity_score +
            self.vm_count_weight * vm_count_score +
            kvm_bonus
        )
        
        return min(total_score, 1.0)

    async def reserve_resources(
        self,
        host_id: str,
        resources: ResourceReservation
    ) -> Optional[str]:
        """
        Reserve resources on a host.
        
        Args:
            host_id: Host identifier
            resources: Resources to reserve
            
        Returns:
            Reservation ID if successful
        """
        async with self._reservation_lock:
            host = self._hosts.get(host_id)
            if not host:
                return None
            
            # Check if host can accommodate
            capacity = host.get_capacity()
            if not capacity.meets_requirements(
                resources.cpu_cores,
                resources.memory_mb,
                resources.storage_gb
            ):
                return None
            
            # Create reservation
            reservation_id = str(uuid.uuid4())
            resources.id = reservation_id
            resources.host_id = host_id
            resources.created_at = datetime.now(timezone.utc)
            
            self._reservations[reservation_id] = resources
            
            logger.info(f"Reserved resources on host {host_id}: {reservation_id}")
            return reservation_id

    async def release_resources(
        self,
        reservation_id: str
    ) -> bool:
        """
        Release a resource reservation.
        
        Args:
            reservation_id: Reservation identifier
            
        Returns:
            True if successful
        """
        async with self._reservation_lock:
            reservation = self._reservations.get(reservation_id)
            if not reservation:
                return False
            
            del self._reservations[reservation_id]
            
            logger.info(f"Released reservation: {reservation_id}")
            return True

    def _meets_requirements(
        self,
        host: Host,
        requirements: VMRequirements
    ) -> bool:
        """Check if a host meets the requirements."""
        # Must be online and not in maintenance
        if host.status != HostStatus.ONLINE:
            return False
        if host.maintenance_mode:
            return False
        
        # Must support the architecture
        if not host.supports_architecture(requirements.architecture):
            return False
        
        # Check KVM requirement
        if requirements.require_kvm and not host.kvm_enabled:
            return False
        
        # Check nested virtualization requirement
        if requirements.require_nested_virt and not host.nested_virt_enabled:
            return False
        
        # Check capacity
        capacity = host.get_capacity()
        if not capacity.meets_requirements(
            requirements.min_cpu_cores,
            requirements.min_memory_mb,
            requirements.min_storage_gb
        ):
            return False
        
        # Check if host can allocate more VMs
        if not host.can_allocate_vm():
            return False
        
        # Check utilization threshold (85%)
        if host.current_utilization.is_overloaded():
            return False
        
        # Check group if specified
        if requirements.group_id and host.group_id != requirements.group_id:
            return False
        
        # Check labels if specified
        if requirements.required_labels:
            for key, value in requirements.required_labels.items():
                if host.labels.get(key) != value:
                    return False
        
        return True

    def _estimate_wait_time(self, requirements: VMRequirements) -> int:
        """Estimate wait time when no hosts are available."""
        # Find hosts that could become available
        potential_hosts = []
        for host in self._hosts.values():
            if host.supports_architecture(requirements.architecture):
                potential_hosts.append(host)
        
        if not potential_hosts:
            return -1  # No hosts can handle this architecture
        
        # Estimate based on average VM count and typical VM lifetime
        avg_vms = sum(h.running_vm_count for h in potential_hosts) / len(potential_hosts)
        estimated_vm_lifetime = 1800  # 30 minutes average VM lifetime
        
        return int(avg_vms * estimated_vm_lifetime / len(potential_hosts))
